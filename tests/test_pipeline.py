import unittest
from pathlib import Path
from support import scratch

ROOT = Path(__file__).resolve().parents[1]


class WriterDouble:
    """External service double; real generation/state/repair logic stays under test."""
    def __init__(self, always_bad=False):
        self.payloads = []
        self.always_bad = always_bad

    def create(self, instructions, payload):
        self.payloads.append(payload)
        blocks = {}
        for e in payload["envelopes"]:
            bad = e["id"] == "b1" and (self.always_bad or len(self.payloads) == 1)
            blocks[e["id"]] = ("Vague transformation improved everything across the business without any clearly explained work or specific result for the team." if bad else "Reduced manual status chasing by building a shared action ledger that recorded routine requests and escalated risky changes to a human.")
        return {"blocks": blocks}

    def decide(self, state, questions):
        result = {}
        for key, q in questions.items():
            block_id = key.split("__")[0]
            bad = "Vague" in state["blocks"][block_id]["text"]
            choice = "FAIL" if bad else "PASS"
            result[key] = {"choice": choice, "probabilities": {x: float(x == choice) for x in q["criteria"]}, "confidence": 1.0}
        return result


def envelope(id):
    return {"id": id, "kind": "bullet", "purpose": "demonstrate operational control", "evidence": [], "max_words": 38}


class GenerationTests(unittest.TestCase):
    def policy(self):
        from harness.decisions import load_policy
        return load_policy(ROOT / "policy" / "decisions.json")

    def test_resume_validates_completed_final_draft_without_rewriting(self):
        from harness.generation import Generation
        from harness.store import RunStore
        class InterruptedJudge(WriterDouble):
            def create(self, instructions, payload):
                result = super().create(instructions, payload)
                if len(self.payloads) < 3:
                    result["blocks"]["b1"] = "Vague draft variant " + str(len(self.payloads))
                return result

            def decide(self, state, questions):
                if len(self.payloads) == 3:
                    raise RuntimeError("simulated classifier interruption")
                return super().decide(state, questions)

        with scratch() as directory:
            store = RunStore(directory)
            writer = InterruptedJudge()
            with self.assertRaisesRegex(RuntimeError, "classifier interruption"):
                Generation(store, writer, self.policy(), 2).realize([envelope("b1")], {})
            resumed = RunStore(directory)
            next_writer = WriterDouble()
            Generation(resumed, next_writer, self.policy(), 2).realize([envelope("b1")], {})
            record = resumed.state["blocks"]["b1"]
            self.assertEqual(record["status"], "ACCEPTED")
            self.assertEqual(record["attempt_count"], 3)
            self.assertEqual([r["attempt"] for r in record["revisions"]], [0, 1, 2])
            self.assertTrue(record["text"].startswith("Reduced manual status chasing"))
            self.assertEqual(len(next_writer.payloads), 0)
            self.assertNotIn("pending_draft", record)

    def test_repairs_only_failed_block_and_preserves_accepted_revision(self):
        from harness.generation import Generation
        from harness.store import RunStore
        with scratch() as directory:
            store = RunStore(directory)
            writer = WriterDouble()
            generation = Generation(store, writer, self.policy(), max_repairs=2)
            generation.realize([envelope("b1"), envelope("b2")], {"role": "AI engineer"})
            self.assertEqual([e["id"] for e in writer.payloads[1]["envelopes"]], ["b1"])
            self.assertEqual(len(store.state["blocks"]["b2"]["revisions"]), 1)
            self.assertEqual(store.state["blocks"]["b1"]["status"], "ACCEPTED")
            original = store.state["blocks"]["b2"]["text"]
            generation.realize([envelope("b1"), envelope("b2")], {"role": "AI engineer"})
            self.assertEqual(len(writer.payloads), 2)
            self.assertEqual(store.state["blocks"]["b2"]["text"], original)

    def test_repair_exhaustion_keeps_draft_and_never_accepts(self):
        from harness.generation import Generation
        from harness.store import RunStore
        with scratch() as directory:
            store = RunStore(directory)
            writer = WriterDouble(always_bad=True)
            Generation(store, writer, self.policy(), max_repairs=2).realize([envelope("b1")], {})
            self.assertLessEqual(len(writer.payloads), 3)
            self.assertEqual(store.state["blocks"]["b1"]["status"], "NEEDS_REVIEW")
            self.assertTrue(store.state["blocks"]["b1"]["text"])

    def test_changed_envelope_invalidates_acceptance(self):
        from harness.generation import Generation
        from harness.store import RunStore
        with scratch() as directory:
            store, writer = RunStore(directory), WriterDouble()
            generation = Generation(store, writer, self.policy(), max_repairs=2)
            generation.realize([envelope("b2")], {"role": "AI engineer"})
            changed = envelope("b2")
            changed["purpose"] = "demonstrate a different requirement"
            generation.realize([changed], {"role": "AI engineer"})
            self.assertEqual(len(writer.payloads), 2)

    def test_resume_does_not_reset_consumed_repair_budget(self):
        from harness.generation import Generation
        from harness.store import RunStore
        class Interrupted(WriterDouble):
            def create(self, instructions, payload):
                if len(self.payloads) == 2:
                    self.payloads.append(payload)
                    raise RuntimeError("simulated interruption")
                result = super().create(instructions, payload)
                result["blocks"]["b1"] += " " + str(len(self.payloads))
                return result
        with scratch() as directory:
            store = RunStore(directory)
            writer = Interrupted(always_bad=True)
            with self.assertRaises(RuntimeError):
                Generation(store, writer, self.policy(), 2).realize([envelope("b1")], {})
            resumed = RunStore(directory)
            next_writer = WriterDouble(always_bad=True)
            Generation(resumed, next_writer, self.policy(), 2).realize([envelope("b1")], {})
            self.assertEqual(len(next_writer.payloads), 0)
            self.assertEqual(resumed.state["blocks"]["b1"]["status"], "NEEDS_REVIEW")


class PlanningTests(unittest.TestCase):
    def test_plan_keeps_every_employer_and_does_not_force_unsupported_proof(self):
        from harness.planning import select_plan
        from harness.sources import load_canonical
        canonical = load_canonical(ROOT / "01-CANONICAL.md")
        requirements = [{"id": "r1", "text": "operational agents", "priority": "CORE"}, {"id": "r2", "text": "unsupported specialist work", "priority": "CORE"}]
        coverage = {e["id"]: {"r1": "DIRECT", "r2": "NO_SUPPORT"} for e in canonical["evidence"]}
        plan = select_plan(canonical, requirements, coverage)
        self.assertEqual({b["employer_id"] for b in plan["blocks"]}, {e["id"] for e in canonical["employers"]})
        self.assertGreaterEqual(len(plan["blocks"]), 8)
        self.assertLessEqual(len(plan["blocks"]), 10)
        self.assertIn("r2", plan["gaps"])
        self.assertFalse(any("r2" in b["requirement_ids"] for b in plan["blocks"]))
        self.assertEqual(len({b["evidence"][0]["id"] for b in plan["blocks"]}), len(plan["blocks"]))


class ReleaseTests(unittest.TestCase):
    def test_resume_refuses_writing_version_mismatch_before_mutation(self):
        import json
        from harness.pipeline import execute
        from harness.store import RunStore
        with scratch() as root:
            (root / "config.json").write_text(json.dumps({"writing_version": 2}), encoding="utf-8")
            folder = root / "jobs" / "old"
            store = RunStore(folder)
            store.state["writing_version"] = 1
            store.save()
            store.write("inputs/config.json", {"writing_version": 1})
            store.write("release.json", {"status": "ACCEPTED_EXPERIMENTAL", "application_hash": "old"})
            before = (folder / "run.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "writing version 1"):
                execute(root, folder)
            self.assertEqual((folder / "run.json").read_bytes(), before)
            self.assertTrue((folder / "release.json").exists())

    def test_old_acceptance_is_archived_before_rerun(self):
        from harness.pipeline import invalidate_release
        from harness.store import RunStore
        with scratch() as directory:
            store = RunStore(directory)
            store.write("release.json", {"status": "ACCEPTED_EXPERIMENTAL", "application_hash": "oldhash"})
            invalidate_release(store)
            self.assertFalse((directory / "release.json").exists())
            self.assertTrue((directory / "releases" / "oldhash.json").exists())
    def test_failed_or_uncertain_gate_never_produces_accepted_status(self):
        from harness.pipeline import release_status
        blocks = {"b1": {"status": "ACCEPTED"}}
        self.assertEqual(release_status(blocks, {"clarity": {"choice": "PASS"}}, True, []), "ACCEPTED_EXPERIMENTAL")
        self.assertEqual(release_status(blocks, {"clarity": {"choice": "UNCERTAIN"}}, True, []), "REVIEW_REQUIRED")
        self.assertEqual(release_status(blocks, {"clarity": {"choice": "PASS"}}, False, []), "REVIEW_REQUIRED")
        blocks["b1"]["status"] = "NEEDS_REVIEW"
        self.assertEqual(release_status(blocks, {"clarity": {"choice": "PASS"}}, True, []), "REVIEW_REQUIRED")

    def test_jd_citations_cannot_reference_invented_text(self):
        from harness.pipeline import validate_job_spans
        draft = {"requirements": [{"text": "Build agents", "quote": "imaginary qualification"}], "stack": []}
        with self.assertRaises(ValueError):
            validate_job_spans(draft, "Build practical AI solutions.")

    def test_capitalized_quote_is_restored_to_exact_source_text(self):
        from harness.pipeline import validate_job_spans
        draft = {"requirements": [{"text": "Build agents", "quote": "Build practical AI solutions."}], "stack": []}
        validate_job_spans(draft, "You will build practical AI solutions.")
        self.assertEqual(draft["requirements"][0]["quote"], "build practical AI solutions.")

    def test_offline_render_never_loads_provider_or_credentials(self):
        from unittest.mock import patch
        from harness.pipeline import render_saved
        from harness.store import RunStore
        from test_rendering import sample_application
        app = sample_application()
        with scratch() as directory:
            store = RunStore(directory)
            store.write("application.json", app)
            store.write("profile.json", {"name": "Test Candidate", "location": "Test City", "phone": "123"})
            (directory / "jd.md").write_text("Example JD", encoding="utf-8")
            with patch("harness.pipeline.OpenRouter", side_effect=AssertionError("Offline render cannot use API")), patch("harness.pipeline.load_key", side_effect=AssertionError("Offline render cannot load key")):
                result = render_saved(directory)
            self.assertEqual(result["status"], "MANUALLY_MODIFIED")
            self.assertTrue((directory / "chat_context.md").exists())


if __name__ == "__main__":
    unittest.main()
