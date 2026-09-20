import unittest
from pathlib import Path
from support import scratch


ROOT = Path(__file__).resolve().parents[1]


class SourceTests(unittest.TestCase):
    def test_operations_retains_employer_status_and_exact_source(self):
        from harness.sources import load_canonical
        data = load_canonical(ROOT / "01-CANONICAL.md")
        unit = next(x for x in data["evidence"] if "Multi-agent operational" in x["heading"])
        self.assertIn("Airtable served as the shared ledger", unit["text"])
        self.assertIn("Do not imply that every planned system was complete", unit["boundaries"])
        self.assertEqual(len(data["employers"]), 4)
        self.assertEqual(data["profile"]["location"], "Mannheim, Germany")
        self.assertNotIn("email", data["profile"])

    def test_think_round_inherits_no_production_launch(self):
        from harness.sources import load_canonical
        data = load_canonical(ROOT / "01-CANONICAL.md")
        units = [x for x in data["evidence"] if x["employer_id"] == "think-round-inc"]
        self.assertGreaterEqual(len(units), 3)
        for unit in units:
            self.assertIn("production launch", unit["boundaries"])
            self.assertIn("not yet approved", unit["boundaries"])


class ProviderTests(unittest.TestCase):
    def test_malformed_decision_shapes_retry_and_reuse_recovered_cache(self):
        from harness.provider import OpenRouter
        from harness.store import RunStore
        questions = {"q": {"criteria": {"PASS": "yes", "FAIL": "no"}}}
        valid = {"answers": {"q": {"choice": "PASS", "probabilities": {"PASS": 1, "FAIL": 0}, "confidence": 1}}}
        malformed = [[], {"answers": None}, {"answers": ["q"]}, {"answers": {"q": None}},
                     {"answers": {"q": {"choice": "PASS", "probabilities": None}}},
                     {"answers": {"q": {"choice": [], "probabilities": {"PASS": 1, "FAIL": 0}}}}]
        for invalid in malformed:
            with self.subTest(response=invalid), scratch() as folder:
                store = RunStore(folder)
                responses = iter([invalid, valid])
                provider = OpenRouter(store, {"classifier_model": "test", "max_requests": 5}, "private-key", lambda *args: next(responses))
                self.assertEqual(provider.decide({}, questions)["q"]["choice"], "PASS")
                self.assertEqual(store.state["http_attempts"], 2)
                resumed = OpenRouter(RunStore(folder), provider.config, "private-key", lambda *args: self.fail("Recovery must reuse the cached valid response"))
                self.assertEqual(resumed.decide({}, questions)["q"]["choice"], "PASS")

    def test_invalid_decision_response_can_recover_without_poisoning_cache(self):
        from harness.provider import OpenRouter
        from harness.store import RunStore
        with scratch() as folder:
            store = RunStore(folder)
            responses = iter([{"answers": {}}, {"answers": {"q": {"choice": "PASS", "probabilities": {"PASS": 1, "FAIL": 0, "UNCERTAIN": 0}, "confidence": 1}}}])
            provider = OpenRouter(store, {"classifier_model": "test", "max_requests": 5}, "private-key", lambda *args: next(responses))
            questions = {"q": {"type": "choice", "instructions": "q", "criteria": {"PASS": "yes", "FAIL": "no", "UNCERTAIN": "unknown"}}}
            self.assertEqual(provider.decide({}, questions)["q"]["choice"], "PASS")
            self.assertEqual(store.state["http_attempts"], 2)
    def test_cache_reuses_completed_response_and_tracks_actual_usage(self):
        from harness.provider import OpenRouter
        from harness.store import RunStore
        with scratch() as folder:
            store = RunStore(Path(folder))
            def transport(url, body, key):
                return {"choices": [{"message": {"content": '{"text":"hello"}'}}], "model": "test-writer", "usage": {"cost": 0.02}}
            provider = OpenRouter(store, {"writer_model": "test-writer", "classifier_model": "test-jev", "max_requests": 5}, "private-key", transport)
            self.assertEqual(provider.create("write", {"task": "greeting"}), {"text": "hello"})
            provider.transport = lambda *args: self.fail("completed response must not call network again")
            self.assertEqual(provider.create("write", {"task": "greeting"}), {"text": "hello"})
            self.assertEqual(store.state["http_attempts"], 1)
            self.assertAlmostEqual(store.state["cost_usd"], .02)
            self.assertNotIn("private-key", "".join(p.read_text() for p in Path(folder).rglob("*.json")))

    def test_malformed_or_missing_classifier_answers_fail_closed(self):
        from harness.provider import validate_decisions
        questions = {"coverage": {"type": "choice", "instructions": "support?", "criteria": {"YES": "supported", "NO": "absent", "UNCERTAIN": "unknown"}}}
        for response in ({"answers": {}}, {"answers": {"coverage": {"choice": "YES", "probabilities": {"YES": 1.0}}}}, {"answers": {"coverage": {"choice": "FAKE", "probabilities": {"YES": 1, "NO": 0, "UNCERTAIN": 0}, "confidence": 1}}}):
            with self.subTest(response=response), self.assertRaises(ValueError):
                validate_decisions(response, questions)

    def test_valid_uncertain_decision_stays_uncertain(self):
        from harness.provider import validate_decisions
        q = {"q": {"criteria": {"PASS": "yes", "FAIL": "no", "UNCERTAIN": "unknown"}}}
        answers = validate_decisions({"answers": {"q": {"choice": "UNCERTAIN", "probabilities": {"PASS": .1, "FAIL": .2, "UNCERTAIN": .7}, "confidence": .4}}}, q)
        self.assertEqual(answers["q"]["choice"], "UNCERTAIN")


class ContractTests(unittest.TestCase):
    def test_external_contract_rejects_extra_keys_and_nonempty_projects(self):
        from harness.models import Application
        from test_rendering import sample_application
        raw = sample_application()
        Application.model_validate(raw)
        raw["debug"] = "should never reach renderer"
        with self.assertRaises(ValueError):
            Application.model_validate(raw)
        raw.pop("debug")
        raw["resume"]["projects"] = [{"name": "invented project"}]
        with self.assertRaises(ValueError):
            Application.model_validate(raw)


if __name__ == "__main__":
    unittest.main()
