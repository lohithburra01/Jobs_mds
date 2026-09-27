import argparse
import json
import sys
import time
from pathlib import Path

from pydantic import ValidationError

from .controller import RunController, kill_tree, process_alive
from .models import Contract, Event, TERMINAL_STATES


def _run(args) -> int:
    source = Path(args.contract).resolve()
    try:
        contract = Contract.model_validate_json(source.read_text(encoding="utf-8"))
        worker = json.loads(args.worker_command) if args.worker_command else None
        if worker is not None and (not isinstance(worker, list) or not worker or not all(isinstance(x, str) and x for x in worker)):
            raise ValueError("--worker-command must be a nonempty JSON string array")
        return RunController(contract, source, worker, args.codex).execute()
    except (OSError, ValueError, ValidationError, json.JSONDecodeError, RuntimeError) as error:
        print(f"devcontrol: {error}", file=sys.stderr)
        return 2


def _load_state(run: Path) -> dict:
    return json.loads((run / "state.json").read_text(encoding="utf-8"))


def _status(args) -> int:
    state = _load_state(Path(args.run).resolve())
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def _stop(args) -> int:
    run = Path(args.run).resolve()
    (run / "STOP").touch(exist_ok=True)
    state = _load_state(run)
    pid = state.get("child_pid")
    if isinstance(pid, int) and process_alive(pid):
        kill_tree(pid)
    print(f"stop requested: {run}")
    return 0


def _events(args) -> int:
    run = Path(args.run).resolve()
    source = run / "events.jsonl"
    position = 0
    while True:
        if source.exists():
            with source.open("r", encoding="utf-8") as events:
                events.seek(position)
                for line in events:
                    item = Event.model_validate_json(line)
                    print(item.model_dump_json())
                position = events.tell()
        if not args.follow:
            return 0
        try:
            if _load_state(run).get("status") in TERMINAL_STATES:
                return 0
        except OSError:
            pass
        time.sleep(.5)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="python -m devcontrol", description="Bounded local coding-task controller")
    commands = root.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--contract", required=True)
    run.add_argument("--worker-command", help="JSON argv array for a local worker fixture")
    run.add_argument("--codex", help="explicit codex executable path")
    run.set_defaults(function=_run)
    for name, function in (("status", _status), ("stop", _stop), ("events", _events)):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        if name == "events":
            command.add_argument("--follow", action="store_true")
        command.set_defaults(function=function)
    return root


def main(argv=None) -> int:
    arguments = parser().parse_args(argv)
    return arguments.function(arguments)
