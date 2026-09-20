import argparse
import json
from pathlib import Path

from harness.comparison import compare_job


def main():
    parser = argparse.ArgumentParser(description="Create one one-shot comparison for a completed v2 job")
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(compare_job(args.root, args.job), indent=2))


if __name__ == "__main__":
    main()
