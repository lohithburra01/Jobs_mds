import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from .pipeline import execute, render_saved, start
from .provider import ProviderError


@contextmanager
def job_lock(folder):
    lock = folder / ".running.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError("This job is already running, or a crashed process left .running.lock. Verify no process is running before removing that lock.") from None
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local resume harness: Jev decides, writer creates")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command")
    new = sub.add_parser("new")
    new.add_argument("--jd", type=Path)
    for name in ("resume", "inspect", "render"):
        sub.add_parser(name).add_argument("job", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command in (None, "new"):
            path = getattr(args, "jd", None)
            if not path:
                print("Paste the JD. Type /done on its own line when finished.")
                lines = []
                for line in sys.stdin:
                    if line.strip() == "/done":
                        break
                    lines.append(line)
                if not "".join(lines).strip():
                    raise ValueError("No JD supplied")
                path = root / "tmp" / "pasted-jd.md"
                path.parent.mkdir(exist_ok=True)
                path.write_text("".join(lines), encoding="utf-8")
            folder, state = start(root, path.resolve())
        elif args.command == "inspect":
            state = json.loads((args.job / "run.json").read_text(encoding="utf-8"))
            coverage = state.get("coverage_summary", {})
            gaps = [item["id"] for item in coverage.get("components", [])
                    if item.get("priority") == "CORE" and item.get("status") != "Explicit"]
            records = state.get("v3_text_records", state.get("blocks", {}))
            print(json.dumps({"status": state["status"], "role": state.get("job_model_v3", state.get("job_model", {})).get("role"),
                              "gaps": gaps or state.get("plan", {}).get("gaps", []), "blocks": {k: v["status"] for k, v in records.items()},
                              "global_checks": {k: v["choice"] for k, v in state.get("global_verdicts", {}).items()},
                              "coverage_report": str(args.job / "coverage.md") if (args.job / "coverage.md").exists() else None,
                              "http_attempts": state["http_attempts"], "logical_jev_questions": state.get("logical_jev_questions", 0),
                              "reported_cost_usd": state["cost_usd"]}, indent=2))
            return 0
        elif args.command == "render":
            with job_lock(args.job):
                rendered = render_saved(args.job)
            print(json.dumps({k: rendered[k] for k in ("status", "resume", "cover_letter", "page_counts")}, indent=2))
            return 0 if rendered["checks"]["passed"] else 2
        else:
            folder = args.job.resolve()
            with job_lock(folder):
                state = execute(root, folder)
        print(json.dumps({"job": str(folder), "status": state["status"], "artifacts": state.get("artifacts"),
                          "http_attempts": state["http_attempts"], "reported_cost_usd": state["cost_usd"]}, indent=2))
        return 0 if state["status"] == "ACCEPTED_EXPERIMENTAL" else 2
    except (ProviderError, ValueError, OSError) as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
