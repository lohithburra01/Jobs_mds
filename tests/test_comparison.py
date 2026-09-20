import copy
import json
import unittest
from pathlib import Path

from support import scratch
from test_rendering import sample_application

ROOT = Path(__file__).resolve().parents[1]


class OneShotProvider:
    def __init__(self, application):
        self.application = application
        self.calls = []

    def create(self, instructions, payload):
        self.calls.append((instructions, payload))
        return copy.deepcopy(self.application)


class ComparisonTests(unittest.TestCase):
    def test_one_shot_uses_one_call_and_does_not_modify_existing_job_files(self):
        from harness.comparison import compare_job
        from harness.store import RunStore
        app = sample_application()
        with scratch() as root:
            folder = root / "jobs" / "case"
            (folder / "inputs").mkdir(parents=True)
            (folder / "jd.md").write_text("Build AI workflows.", encoding="utf-8")
            (folder / "profile.json").write_text(json.dumps({"name": "Ada", "location": "Berlin", "phone": "123"}), encoding="utf-8")
            (folder / "writing-plan.json").write_text(json.dumps([{"id": "b1", "evidence": [{"text": "Built workflows", "boundaries": "Keep scope"}]}]), encoding="utf-8")
            (folder / "inputs" / "canonical.md").write_text((ROOT / "01-CANONICAL.md").read_text(encoding="utf-8"), encoding="utf-8")
            (folder / "inputs" / "config.json").write_text(json.dumps({"writer_model": "test"}), encoding="utf-8")
            store = RunStore(folder)
            store.state.update({"application_date": "September 20, 2026", "job_model": {"company": app["company_name"], "role": "Engineer"}, "writing_version": 2})
            store.save()
            before = {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
            provider = OneShotProvider(app)
            result = compare_job(root, folder, provider=provider)
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(result["status"], "RENDERED_ONE_SHOT")
            self.assertEqual(result["page_counts"], {"resume": 1, "cover_letter": 1})
            self.assertNotIn("current_document", provider.calls[0][1])
            for relative, content in before.items():
                self.assertEqual((folder / relative).read_bytes(), content)

    def test_invalid_one_shot_is_recorded_without_second_call(self):
        from harness.comparison import compare_job
        from harness.store import RunStore
        with scratch() as root:
            folder = root / "jobs" / "case"
            (folder / "inputs").mkdir(parents=True)
            (folder / "jd.md").write_text("Build AI workflows.", encoding="utf-8")
            (folder / "profile.json").write_text(json.dumps({"name": "Ada", "location": "Berlin", "phone": "123"}), encoding="utf-8")
            (folder / "writing-plan.json").write_text("[]", encoding="utf-8")
            (folder / "inputs" / "canonical.md").write_text((ROOT / "01-CANONICAL.md").read_text(encoding="utf-8"), encoding="utf-8")
            (folder / "inputs" / "config.json").write_text(json.dumps({"writer_model": "test"}), encoding="utf-8")
            store = RunStore(folder)
            store.state.update({"application_date": "September 20, 2026", "job_model": {"company": "Acme", "role": "Engineer"}, "writing_version": 2})
            store.save()
            provider = OneShotProvider({"bad": "shape"})
            result = compare_job(root, folder, provider=provider)
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(result["status"], "INVALID_ONE_SHOT")
            self.assertTrue(Path(result["report"]).exists())


if __name__ == "__main__":
    unittest.main()
