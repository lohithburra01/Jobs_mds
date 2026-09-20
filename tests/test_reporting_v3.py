import unittest

from support import scratch
from test_run_v3 import V3Provider, make_blueprint


class ReportingV3Tests(unittest.TestCase):
    def test_report_lists_every_component_skill_employer_project_and_local_check(self):
        from harness.generation import run_writing_v3
        from harness.records import AssessmentV3, LayoutSelection
        from harness.reporting import write_coverage_report
        from harness.store import RunStore
        blueprint = make_blueprint()
        with scratch() as directory:
            store = RunStore(directory)
            result = run_writing_v3(store, V3Provider(store), {}, blueprint,
                                    {"name": "Ada", "location": "Berlin", "phone": "1"})
            data = write_coverage_report(directory, blueprint,
                                         AssessmentV3.model_validate(result["assessment"]),
                                         LayoutSelection.model_validate(result["layout"]),
                                         {"http_attempts": 1, "logical_jev_questions": 10,
                                          "reported_cost_usd": 0.01})
            self.assertEqual(len(data["components"]), len(blueprint.job.components))
            self.assertEqual(len(data["employers"]), 4)
            self.assertEqual(data["project"]["period"], "")
            markdown = (directory / "coverage.md").read_text(encoding="utf-8")
            self.assertIn("These are local layout checks, not an ATS-pass", markdown)
            self.assertIn("Python", markdown)
            self.assertTrue((directory / "coverage.json").exists())


if __name__ == "__main__":
    unittest.main()
