"""Validate canonical v3 and its exact migration coverage."""

from __future__ import annotations

import json
from pathlib import Path

from harness.canonical import check_migration, load_canonical_v3


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    canonical = load_canonical_v3(root / "canonical.yaml")
    result = check_migration(canonical, root / canonical.source_archive)
    (root / "migration-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
