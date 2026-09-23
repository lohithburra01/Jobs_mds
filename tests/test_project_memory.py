"""Recovery and data-integrity checks; these do not judge resume quality."""
import json
from pathlib import Path
import subprocess
import sys
import shutil
import uuid
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "project_memory.py"


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "tmp" / "memory-tests" / uuid.uuid4().hex
        self.root.mkdir(parents=True)

    def tearDown(self):
        assert self.root.resolve().is_relative_to((ROOT / "tmp" / "memory-tests").resolve())
        shutil.rmtree(self.root)

    def cli(self, *args, ok=True):
        p = subprocess.run([sys.executable, str(CLI), "--root", str(self.root), *args],
                           capture_output=True, text=True, encoding="utf-8")
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def put(self, record, revision=0, ok=True):
        path = self.root / "input.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return self.cli("put", "--file", str(path), "--expected-revision", str(revision),
                        "--reason", "User requested memory fixture", ok=ok)

    def record(self, ident, **changes):
        return dict(id=ident, kind="task", title=ident, summary="Standalone explanation for " + ident,
                    status="planned", body="", links=[], **changes)

    def test_fresh_process_and_rebuild_preserve_revisions(self):
        r = self.record("task-1")
        self.put(r)
        r["summary"] = "Updated explanation, not an append-only summary"
        self.put(r, 1)
        stale = self.put(r, 1, ok=False)
        self.assertNotEqual(stale.returncode, 0)
        self.cli("rebuild")
        current = json.loads(self.cli("show", "task-1").stdout)
        self.assertEqual(current["revision"], 2)
        old = json.loads(self.cli("show", "task-1", "--revision", "1").stdout)
        self.assertNotEqual(old["summary"], current["summary"])

    def test_known_impact_traverses_dependencies_not_unrelated_tasks(self):
        self.put(self.record("decision-1"))
        a = self.record("task-1")
        a["links"] = [{"rel": "depends_on", "to": "decision-1"}]
        self.put(a)
        b = self.record("task-2")
        b["links"] = [{"rel": "depends_on", "to": "task-1"}]
        self.put(b)
        self.put(self.record("unrelated"))
        result = json.loads(self.cli("impact", "decision-1").stdout)
        self.assertEqual(set(result["affected_ids"]), {"task-1", "task-2"})

    def test_invalid_ids_dangling_links_and_false_acceptance_rejected(self):
        self.assertNotEqual(self.put(self.record("../escape"), ok=False).returncode, 0)
        r = self.record("task-1")
        r["links"] = [{"rel": "depends_on", "to": "missing"}]
        self.assertNotEqual(self.put(r, ok=False).returncode, 0)
        r["links"] = []
        r["status"] = "accepted"
        self.assertNotEqual(self.put(r, ok=False).returncode, 0)

    def test_source_changes_are_visible_not_silently_reinterpreted(self):
        source = self.root / "agreement.txt"
        source.write_text("First line\nExact agreed rule\n", encoding="utf-8")
        self.cli("import-source", "agreement.txt", "--id", "source-agreement", "--status", "reference")
        source.write_text("Changed rule\n", encoding="utf-8")
        result = json.loads(self.cli("doctor", ok=False).stdout)
        self.assertTrue(any("source" in str(x).lower() for x in result["problems"]))

    def test_event_is_durable_and_does_not_change_task(self):
        self.put(self.record("task-1"))
        self.cli("event", "--kind", "interrupted", "--summary", "Stopped before completion", "--record", "task-1")
        events = json.loads(self.cli("timeline", "--limit", "1").stdout)
        self.assertEqual(events[0]["kind"], "interrupted")
        self.assertEqual(json.loads(self.cli("show", "task-1").stdout)["status"], "planned")


if __name__ == "__main__":
    unittest.main()
