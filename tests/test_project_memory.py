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
sys.path.insert(0, str(ROOT))
from project_memory.store import Store, digest


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
        p = self.record("project")
        p.update(kind="project", focus="missing", checkpoints=[])
        self.assertNotEqual(self.put(p, ok=False).returncode, 0)
        self.assertRaises(ValueError, Store(self.root).path, ".ENV")
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

    def test_corrupt_record_cannot_be_treated_as_new_and_overwritten(self):
        self.put(self.record("task-1"))
        record = self.root / "project-memory/records/task-1/000001.json"
        record.write_text('{"broken":', encoding="utf-8")
        self.assertNotEqual(self.put(self.record("task-1"), 0, ok=False).returncode, 0)
        self.assertEqual(record.read_text(encoding="utf-8"), '{"broken":')

    def test_interrupted_first_write_is_reported_without_breaking_other_records(self):
        self.put(self.record("task-1"))
        partial = self.root / "project-memory/records/interrupted"
        partial.mkdir()
        (partial / ".unfinished.tmp").write_text("partial", encoding="utf-8")
        self.assertEqual(len(json.loads(self.cli("search", "task-1").stdout)), 1)
        report = json.loads(self.cli("doctor", ok=False).stdout)
        self.assertTrue(report["problems"])

    def test_corrupt_cache_rebuilds_without_losing_saved_records(self):
        self.put(self.record("task-1"))
        (self.root / "project-memory/cache/memory.sqlite3").write_bytes(b"not a database")
        self.cli("rebuild")
        self.assertEqual(json.loads(self.cli("search", "task-1").stdout)[0]["id"], "task-1")

    def test_torn_event_does_not_swallow_next_event(self):
        store = Store(self.root)
        store.event("before", "Before interruption")
        log = next((store.home / "events").glob("*.jsonl"))
        with log.open("ab") as f:
            f.write(b'{"partial":"\xe2')
        store.event("after", "Recovered")
        rows = store.timeline(4)
        self.assertEqual(rows[0]["kind"], "after")
        self.assertTrue(any(r["kind"] == "damaged_event" for r in rows))

    def test_invalid_source_references_are_rejected_before_saving(self):
        source = self.root / "agreement.txt"
        source.write_text("First\nSecond\n", encoding="utf-8")
        valid = dict(path="agreement.txt", sha256=digest(source.read_bytes()), start=1, end=2)
        invalid = [None, {}, dict(valid, path=None), dict(valid, path=""),
                   dict(valid, sha256=None), dict(valid, sha256="not-a-hash"),
                   dict(valid, sha256="0" * 64), dict(valid, start=0),
                   dict(valid, start=True), dict(valid, start="1"),
                   dict(valid, end=1.5), dict(valid, start=2, end=1),
                   dict(valid, start=99, end=100), dict(valid, end=3)]
        for index, reference in enumerate(invalid):
            with self.subTest(reference=reference):
                record = self.record("invalid-source-" + str(index), sources=[reference])
                result = self.put(record, ok=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((self.root / "project-memory/records" / record["id"]).exists())
        self.put(self.record("valid-source", sources=[valid]))
        self.assertEqual(self.cli("source", "valid-source").stdout, "First\nSecond\n\n")

    def test_source_retrieval_rejects_invalid_line_ranges(self):
        source = self.root / "agreement.txt"
        source.write_text("First\nSecond\n", encoding="utf-8")
        valid = dict(path="agreement.txt", sha256=digest(source.read_bytes()))
        for bounds in ({"start": 0}, {"start": 2, "end": 1}, {"end": 3}, {"start": 99}):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                Store(self.root).source_text(dict(valid, **bounds))

    def test_doctor_reports_corrupt_historical_revision(self):
        record = self.record("task-1")
        self.put(record)
        self.put(dict(record, summary="Current readable version"), 1)
        old = self.root / "project-memory/records/task-1/000001.json"
        old.write_text('{"broken":', encoding="utf-8")
        result = self.cli("doctor", ok=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("000001.json", json.loads(result.stdout)["problems"][0])
        self.assertEqual(json.loads(self.cli("show", "task-1").stdout)["revision"], 2)

    def test_doctor_reports_malformed_current_and_historical_records(self):
        malformed = [[], {}, {"id": "wrong-record"},
                     dict(self.record("task-1"), revision=1, sources=[{"path": "missing.txt"}]),
                     dict(self.record("task-1"), revision=1, links=[None])]
        for value in malformed:
            for revision in (1, 2):
                with self.subTest(value=value, revision=revision):
                    directory = self.root / "project-memory/records/task-1"
                    directory.mkdir(parents=True, exist_ok=True)
                    for number in (1, 2):
                        item = dict(self.record("task-1"), revision=number)
                        if number == revision:
                            item = value
                        (directory / f"{number:06d}.json").write_text(json.dumps(item), encoding="utf-8")
                    result = self.cli("doctor", ok=False)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertTrue(json.loads(result.stdout)["problems"])
                    self.assertNotIn("Traceback", result.stderr)
                    if revision == 2:
                        shown = self.cli("show", "task-1", ok=False)
                        self.assertEqual(shown.returncode, 2)
                        self.assertNotIn("Traceback", shown.stderr)

    def test_doctor_keeps_superseded_source_revisions_as_history(self):
        source = self.root / "agreement.txt"
        source.write_text("Original\nMore lines\n", encoding="utf-8")
        old_reference = dict(path="agreement.txt", sha256=digest(source.read_bytes()), start=1, end=2)
        record = self.record("task-1", sources=[old_reference])
        self.put(record)
        source.write_text("Replacement\n", encoding="utf-8")
        new_reference = dict(path="agreement.txt", sha256=digest(source.read_bytes()), start=1, end=1)
        self.put(dict(record, sources=[new_reference]), 1)
        self.assertEqual(json.loads(self.cli("doctor").stdout)["problems"], [])
        with self.assertRaises(ValueError):
            Store(self.root).source_text(old_reference)


if __name__ == "__main__":
    unittest.main()
