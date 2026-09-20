import unittest
from pathlib import Path

from support import scratch

ROOT = Path(__file__).resolve().parents[1]


def letter(block_id, role):
    return {"id": block_id, "kind": "letter", "role": role, "purpose": role,
            "evidence": [{"id": "source", "text": "Built a supported workflow.", "boundaries": "No invented results."}],
            "target_words": 45, "max_words": 60, "target_terms": [],
            "primary_requirement_id": None, "potential_requirement_ids": []}


class RepairProvider:
    config = {"writer_model": "writer-double"}

    def __init__(self, cycle=False, fail_first=False):
        self.creates = []
        self.cycle = cycle
        self.fail_first = fail_first

    def create(self, instructions, payload):
        self.creates.append(payload)
        if self.fail_first and len(self.creates) == 1:
            raise RuntimeError("interrupted before response")
        result = {}
        for envelope in payload["envelopes"]:
            block_id = envelope["id"]
            if len(self.creates) == 1:
                result[block_id] = "Shared detailed workflow story"
            elif self.cycle:
                result[block_id] = "Shared detailed workflow story" if len(self.creates) == 2 else "Temporary alternative"
            elif block_id == "letter_1":
                result[block_id] = "I build practical AI systems that turn manual business work into controlled workflows."
            else:
                result[block_id] = "Shared detailed workflow story"
        return {"blocks": result}

    def decide(self, state, questions):
        result = {}
        for qid, question in questions.items():
            options = list(question["criteria"])
            if qid.startswith("rel:"):
                case = state["items"][state["case_refs"][qid]]
                answer = "REDUNDANT" if case["left"]["text"] == case["right"]["text"] else "DISTINCT"
            elif qid.startswith("global:") or qid.startswith("local:"):
                answer = "PASS"
            else:
                answer = options[0]
            result[qid] = {"choice": answer, "probabilities": {x: float(x == answer) for x in options}, "confidence": 1.0}
        return result


class WritingRoundTests(unittest.TestCase):
    def policy(self):
        from harness.decisions import load_policy
        return load_policy(ROOT / "policy" / "decisions.json")

    def test_document_repetition_repairs_only_opening_with_proof_visible(self):
        from harness.generation import run_writing
        from harness.store import RunStore
        envelopes = [letter("letter_1", "opening"), letter("letter_2", "proof")]
        with scratch() as directory:
            store, provider = RunStore(directory), RepairProvider()
            texts = run_writing(store, provider, self.policy(), envelopes, {"role": "AI Engineer"}, {"requirements": []})
            self.assertEqual(len(provider.creates), 2)
            self.assertEqual(provider.creates[1]["writable_ids"], ["letter_1"])
            self.assertIn("letter_2", provider.creates[1]["current_document"])
            self.assertEqual(texts["letter_2"], "Shared detailed workflow story")
            self.assertEqual(store.state["blocks"]["letter_2"]["attempt_count"], 1)
            self.assertEqual(store.state["writing_assessment"]["passed"], True)
            self.assertEqual([x["stage"] for x in store.state["stage_usage"]],
                             ["writing_initial", "repair_round_1"])

    def test_interruption_does_not_reset_reserved_writer_attempt(self):
        from harness.generation import run_writing
        from harness.store import RunStore
        envelopes = [letter("letter_1", "opening"), letter("letter_2", "proof")]
        with scratch() as directory:
            store, interrupted = RunStore(directory), RepairProvider(fail_first=True)
            with self.assertRaises(RuntimeError):
                run_writing(store, interrupted, self.policy(), envelopes, {}, {"requirements": []})
            self.assertEqual(store.state["blocks"]["letter_1"]["attempt_count"], 1)
            resumed, provider = RunStore(directory), RepairProvider()
            run_writing(resumed, provider, self.policy(), envelopes, {}, {"requirements": []})
            self.assertGreaterEqual(resumed.state["blocks"]["letter_1"]["attempt_count"], 2)

    def test_stage_usage_keeps_pre_interruption_calls_after_reopen(self):
        from harness.store import RunStore
        with scratch() as directory:
            store = RunStore(directory)
            store.begin_stage("writing_initial")
            store.state["http_attempts"] = 7
            store.state["cost_usd"] = 0.0125
            store.save()

            resumed = RunStore(directory)
            resumed.state["http_attempts"] = 9
            resumed.state["cost_usd"] = 0.015
            resumed.record_stage("writing_initial")

            entry = resumed.state["stage_usage"][0]
            self.assertEqual(entry["http_attempts"], 9)
            self.assertAlmostEqual(entry["reported_cost_usd"], 0.015)
            self.assertNotIn("writing_initial", resumed.state["pending_stage_usage"])

    def test_identical_failed_repair_stops_without_fourth_attempt(self):
        from harness.generation import run_writing
        from harness.store import RunStore
        envelopes = [letter("letter_1", "opening"), letter("letter_2", "proof")]
        with scratch() as directory:
            store, provider = RunStore(directory), RepairProvider(cycle=True)
            run_writing(store, provider, self.policy(), envelopes, {}, {"requirements": []})
            self.assertLessEqual(store.state["blocks"]["letter_1"]["attempt_count"], 3)
            self.assertEqual(store.state["blocks"]["letter_1"]["status"], "NEEDS_REVIEW")


if __name__ == "__main__":
    unittest.main()
