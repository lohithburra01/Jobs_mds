"""Direct entry point; works without installing the application package."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_memory.store import Store, dump


def main():
    parser = argparse.ArgumentParser(description="Local project memory: no model calls, no network.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "context"):
        p = sub.add_parser(name)
        p.add_argument("--id")
    p = sub.add_parser("show")
    p.add_argument("id")
    p.add_argument("--revision", type=int)
    p = sub.add_parser("source")
    p.add_argument("id")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=12)
    p = sub.add_parser("put")
    p.add_argument("--file", required=True)
    p.add_argument("--expected-revision", type=int, required=True)
    p.add_argument("--reason", required=True)
    p = sub.add_parser("event")
    p.add_argument("--kind", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--record")
    p = sub.add_parser("timeline")
    p.add_argument("--limit", type=int, default=15)
    p = sub.add_parser("impact")
    p.add_argument("id")
    p = sub.add_parser("import-source")
    p.add_argument("path")
    p.add_argument("--id", required=True)
    p.add_argument("--status", default="reference")
    p.add_argument("--snapshot", action="store_true")
    sub.add_parser("rebuild")
    sub.add_parser("doctor")
    args = parser.parse_args()
    store = Store(args.root)
    if args.command in ("start", "context"):
        print(store.brief(args.id))
        return 0
    if args.command == "show":
        result = store.get(args.id, args.revision)
    elif args.command == "source":
        r = store.get(args.id)
        print("\n".join(store.source_text(s) for s in r.get("sources", [])))
        return 0
    elif args.command == "put":
        result = store.put(json.loads(Path(args.file).read_text(encoding="utf-8-sig")), args.expected_revision, args.reason)
    elif args.command == "search":
        result = store.search(args.query, args.limit)
    elif args.command == "event":
        result = store.event(args.kind, args.summary, args.record)
    elif args.command == "timeline":
        result = store.timeline(args.limit)
    elif args.command == "impact":
        result = store.impact(args.id)
    elif args.command == "rebuild":
        result = store.rebuild()
    elif args.command == "doctor":
        result = store.doctor()
    elif args.command == "import-source":
        result = store.import_source(args.path, args.id, args.status, args.snapshot)
    print(dump(result), end="")
    return 1 if args.command == "doctor" and result["problems"] else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print("Memory error: " + str(exc), file=sys.stderr)
        sys.exit(2)
