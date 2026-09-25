"""Codex adapter: metadata-only observations and a bounded startup briefing."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_memory.store import Store, digest, now
from project_memory.views import dashboard


def handle(store, payload, synthetic=False):
    kind = str(payload.get("hook_event_name", "Unknown"))
    session = str(payload.get("session_id", "unknown"))
    tool = str(payload.get("tool_name", ""))
    call = str(payload.get("tool_use_id", ""))
    origin = "synthetic" if synthetic else "codex_hook"
    extra = dict(origin=origin, session=session, tool=tool, call=call,
                 turn=payload.get("turn_id"), model=payload.get("model"),
                 transcript_path=payload.get("transcript_path"))
    inputs = payload.get("tool_input", {})
    extra["input_sha256"] = digest(json.dumps(inputs, sort_keys=True).encode())
    if isinstance(inputs, dict):
        command = str(inputs.get("command", inputs.get("cmd", "")))
        verb = re.match(r"^\s*([A-Za-z][A-Za-z0-9_-]{0,60})(?:\s|$)", command)
        extra["command_verb"] = verb.group(1) if verb else None
        extra["input_fields"] = sorted(inputs)
    response = payload.get("tool_response")
    extra["exit_code"] = response.get("exit_code") if isinstance(response, dict) and isinstance(response.get("exit_code"), int) else None
    extra["tool_error"] = response.get("isError") if isinstance(response, dict) and isinstance(response.get("isError"), bool) else None
    if kind == "PostToolUse":
        starts = [x for x in store.timeline(1000) if x.get("kind") == "PreToolUse" and x.get("session") == session and x.get("call") == call and x.get("origin") == origin]
        extra["elapsed_ms"] = max(0, int((datetime.fromisoformat(now()) - datetime.fromisoformat(starts[0]["time"])).total_seconds()*1000)) if starts else None
    try:
        focus = store.get("project")["focus"]
    except ValueError:
        focus = None
    store.event(kind, (kind + (": " + tool if tool else "") + (" (" + extra["command_verb"] + ")" if extra.get("command_verb") else "")), focus, **extra)
    result = {}
    if kind in {"SessionStart", "PostCompact"}:
        result = {"hookSpecificOutput": {"hookEventName": kind, "additionalContext": store.brief()}}
    elif kind in {"PreCompact", "Stop"}:
        result = {"systemMessage": "Project memory: save any new decisions, feedback, current task and next action before handoff. Run project-memory health; do not mark user acceptance yourself."}
    try:
        dashboard(store)
    except ValueError:
        pass  # During initial setup there may be no project root record yet.
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    root = Path(args.root).resolve()
    if not Path(payload.get("cwd", str(root))).resolve().is_relative_to(root):
        print("{}")
        return
    print(json.dumps(handle(Store(root), payload, args.synthetic), ensure_ascii=False))


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except Exception as exc:
        print("Project memory hook failed: " + str(exc), file=sys.stderr)
        sys.exit(1)
