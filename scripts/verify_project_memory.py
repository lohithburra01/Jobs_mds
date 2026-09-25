"""Small repeatable continuity check. No application runs or model calls."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from project_memory.store import Store, now, dump
from project_memory.views import health, dashboard


def main():
    s = Store(ROOT)
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_project_memory*.py"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    agreement = s.get("source-agreement")
    raw = s.path(agreement["sources"][0]["path"]).read_bytes()
    original = (ROOT / "Agreed discussion - verbatim notes - 2026-09-22.txt").read_bytes()
    sections = sorted([r for r in s.all() if r["id"].startswith("source-agreement-")], key=lambda r: r["sources"][0]["start"])
    rebuilt = "".join(s.source_text(r["sources"][0]) for r in sections)
    integrity = s.doctor()
    report = {
        "time": now(), "test_exit_code": tests.returncode, "test_output": tests.stdout + tests.stderr,
        "source_snapshot_byte_identical": raw == original,
        "agreement_sections": len(sections),
        "sections_reconstruct_whole_agreement": rebuilt == raw.decode("utf-8-sig"),
        "brief_characters": len(s.brief()), "integrity": integrity, "observations": health(s),
        "limits": ["No paid model or application generation was run.", "Synthetic hook calls prove handler behavior, not live Codex dispatch.", "No claim that resumes are improved or that Lohith accepted this checkpoint."]
    }
    folder = s.home / "verification"
    folder.mkdir(exist_ok=True)
    target = folder / (report["time"][:10] + "-continuity.json")
    target.write_text(dump(report), encoding="utf-8")
    dashboard(s)
    print(dump({k: v for k,v in report.items() if k not in {"test_output","observations"}}))
    return 1 if tests.returncode or raw != original or rebuilt != raw.decode("utf-8-sig") or integrity["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
