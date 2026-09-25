"""Install project-local observation hooks; never modify trust or permissions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / ".codex" / "hooks.json"
EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "PostCompact", "Stop", "Interrupt", "SessionEnd")


def main():
    config = json.loads(TARGET.read_text(encoding="utf-8-sig")) if TARGET.exists() else {}
    command = 'powershell.exe -NoProfile -NonInteractive -File "' + str(ROOT / "scripts" / "memory-hook.ps1") + '"'
    hooks = config.setdefault("hooks", {})
    for event in EVENTS:
        groups = hooks.setdefault(event, [])
        if not any(h.get("command") == command for group in groups for h in group.get("hooks", [])):
            handler = dict(type="command", command=command, timeout=3 if event in {"Interrupt", "SessionEnd"} else 15)
            if event in {"SessionStart", "PostCompact"}:
                handler["additionalContextLimit"] = 11000
            groups.append({"hooks": [handler]})
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print("Installed " + str(TARGET))
    print("Not automatically trusted. Review /hooks in Codex CLI. Run project-memory health after a new session.")


if __name__ == "__main__":
    main()
