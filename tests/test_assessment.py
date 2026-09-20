import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DecisionDouble:
    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        self.question_ids = []

    def decide(self, state, questions):
        self.question_ids.extend(questions)
        answers = {}
        for qid, question in questions.items():
            options = list(question["criteria"])
            choice = self.overrides.get(qid)
            if choice is None:
                if qid.startswith("rel:"):
                    choice = "DISTINCT"
                elif qid.startswith("req:") and qid.endswith(":state"):
                    choice = "PRESENT"
                elif qid.startswith("req:"):
                    choice = "YES"
                elif qid.startswith("length:"):
                    choice = "NECESSARY"
                else:
                    choice = "PASS"
            answers[qid] = {"choice": choice,
                            "probabilities": {x: float(x == choice) for x in options},
                            "confidence": 1.0}
        return answers


class CaptureDouble(DecisionDouble):
    def __init__(self):
        super().__init__()
        self.states = []

    def decide(self, state, questions):
        self.states.append(state)
        return super().decide(state, questions)


def envelope(block_id, kind="letter", role=None, words=20, primary=None):
    return {"id": block_id, "kind": kind, "role": role or kind,
            "purpose": "Do this block's one job.", "evidence": [{"id": block_id + ":source", "text": "Supported work", "boundaries": "Keep scope"}],
            "max_words": 38 if kind == "bullet" else 60, "target_words": 32,
            "primary_requirement_id": primary, "potential_requirement_ids": [primary] if primary else [],
            "coverage": {primary: "DIRECT"} if primary else {}, "_words": words}


def words(count):
    return " ".join(f"w{i}" for i in range(count))


class AssessmentTests(unittest.TestCase):
    def policy(self):
        from harness.decisions import load_policy
        return load_policy(ROOT / "policy" / "decisions.json")

    def records(self, envelopes):
        return {e["id"]: {"attempt_count": 1, "status": "DRAFTED"} for e in envelopes}

    def test_redundant_opening_and_proof_repairs_opening_only(self):
        from harness.assessment import assess, repair_targets
        envelopes = [envelope("letter_1", role="opening"), envelope("letter_2", role="proof")]
        provider = DecisionDouble({"rel:letter_1:letter_2": "REDUNDANT"})
        report = assess(provider, self.policy(), envelopes,
                        {"letter_1": "same story", "letter_2": "same story"}, {"requirements": []})
        self.assertEqual(repair_targets(report, self.records(envelopes)), ["letter_1"])

    def test_resume_to_letter_reuse_is_not_checked_as_repetition(self):
        from harness.assessment import assess
        envelopes = [envelope("job_1", "bullet", "experience"), envelope("letter_2", role="proof")]
        provider = DecisionDouble()
        assess(provider, self.policy(), envelopes, {e["id"]: "same story" for e in envelopes}, {"requirements": []})
        self.assertFalse(any(q.startswith("rel:job_1:letter") for q in provider.question_ids))

    def test_summary_repetition_repairs_summary_and_leaves_bullet(self):
        from harness.assessment import assess, repair_targets
        envelopes = [envelope("job_1", "bullet", "experience"), envelope("summary", "summary", "summary")]
        provider = DecisionDouble({"rel:summary:job_1": "REDUNDANT"})
        report = assess(provider, self.policy(), envelopes, {e["id"]: "same" for e in envelopes}, {"requirements": []})
        self.assertEqual(repair_targets(report, self.records(envelopes)), ["summary"])

    def test_global_failure_without_local_issue_does_not_guess_a_target(self):
        from harness.assessment import assess, repair_targets
        envelopes = [envelope("letter_3", role="closing")]
        report = assess(DecisionDouble({"global:readability": "FAIL"}), self.policy(), envelopes,
                        {"letter_3": "Readable but globally rejected"}, {"requirements": []})
        self.assertEqual(repair_targets(report, self.records(envelopes)), [])

    def test_missing_named_requirement_targets_its_primary_owner(self):
        from harness.assessment import assess, repair_targets
        envelopes = [envelope("job_1", "bullet", "experience", primary="r1")]
        job = {"requirements": [{"id": "r1", "text": "Deploy systems", "priority": "CORE"}]}
        report = assess(DecisionDouble({"req:r1:state": "ABSENT", "req:r1:job_1": "NO"}),
                        self.policy(), envelopes, {"job_1": "Built a prototype"}, job)
        self.assertEqual(repair_targets(report, self.records(envelopes)), ["job_1"])

    def test_uncertain_relationship_is_review_only(self):
        from harness.assessment import assess, repair_targets
        envelopes = [envelope("letter_1", role="opening"), envelope("letter_2", role="proof")]
        report = assess(DecisionDouble({"rel:letter_1:letter_2": "UNCERTAIN"}), self.policy(), envelopes,
                        {e["id"]: "text" for e in envelopes}, {"requirements": []})
        self.assertEqual(repair_targets(report, self.records(envelopes)), [])
        self.assertTrue(report["unresolved"])

    def test_35_words_requires_semantic_trim_decision(self):
        from harness.assessment import assess, repair_targets
        e = envelope("job_1", "bullet", "experience")
        report = assess(DecisionDouble(), self.policy(), [e], {"job_1": words(35)}, {"requirements": []})
        self.assertEqual(repair_targets(report, self.records([e])), [])
        report = assess(DecisionDouble({"length:job_1": "UNNECESSARY"}), self.policy(), [e],
                        {"job_1": words(35)}, {"requirements": []})
        self.assertEqual(repair_targets(report, self.records([e])), ["job_1"])

    def test_39_words_is_too_long_with_specific_feedback(self):
        from harness.assessment import assess
        e = envelope("job_1", "bullet", "experience")
        report = assess(DecisionDouble(), self.policy(), [e], {"job_1": words(39)}, {"requirements": []})
        issue = next(x for x in report["block_issues"] if x["code"] == "TOO_LONG")
        self.assertIn("39 words", issue["instruction"])
        self.assertIn("7", issue["instruction"])

    def test_batched_cases_deduplicate_shared_state(self):
        from harness.assessment import _decision_cases
        from harness.decisions import choice
        provider = CaptureDouble()
        shared = {"evidence": "x" * 20000}
        verdict = {"PASS": "yes", "FAIL": "no"}
        cases = [("a", shared, choice("First", verdict)), ("b", shared, choice("Second", verdict))]
        _decision_cases(provider, cases)
        self.assertEqual(len(provider.states), 1)
        self.assertEqual(len(provider.states[0]["items"]), 1)
        self.assertEqual(set(provider.states[0]["case_refs"]), {"a", "b"})


if __name__ == "__main__":
    unittest.main()
