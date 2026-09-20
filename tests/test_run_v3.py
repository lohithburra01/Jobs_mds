import unittest

from harness.records import SkillGroup, SkillItem, SkillKind
from support import scratch
from test_planning_v3 import twelve_candidate_case


class V3Provider:
    def __init__(self, store, forbid_create=False):
        self.store = store
        self.config = {"writer_model": "test-writer"}
        self.forbid_create = forbid_create
        self.create_calls = []
        self.decide_calls = []

    def create(self, instructions, payload):
        if self.forbid_create:
            raise AssertionError("saved pending writer response must be resumed")
        self.create_calls.append(payload)
        texts = {}
        for item_id in payload["writable_ids"]:
            if item_id.startswith("summary."):
                texts[item_id] = "AI engineer building reliable production workflows for complex business operations."
            elif item_id.startswith("experience."):
                texts[item_id] = "Built and validated a distinct workflow with a concrete operational result."
            elif item_id.startswith("project."):
                texts[item_id] = "Built a local workflow and validated its inspectable output."
            else:
                texts[item_id] = "I can apply this experience to the role through clear engineering ownership and collaboration."
        return {"texts": texts}

    def decide(self, state, questions):
        self.decide_calls.append(questions)
        answers = {}
        for question_id, question in questions.items():
            selected = next(iter(question["criteria"]))
            answers[question_id] = {"choice": selected,
                                    "probabilities": {key: float(key == selected) for key in question["criteria"]},
                                    "confidence": 1.0}
        return answers


def make_blueprint():
    from harness.planning_v3 import build_blueprint
    canonical, job, decisions = twelve_candidate_case()
    skill = SkillItem(id="s1", exact_term="Python", jd_quote="Python", kind=SkillKind.LANGUAGE,
                      display_group="Languages & interfaces", centrality="CORE", display_text="Python")
    group = SkillGroup(id="g1", label="Languages & interfaces", item_ids=["s1"])
    return build_blueprint(canonical, job, [skill], [group], decisions)


class WritingCoordinatorTests(unittest.TestCase):
    def test_one_coherent_initial_writer_call_produces_ready_result(self):
        from harness.generation import run_writing_v3
        from harness.store import RunStore
        blueprint = make_blueprint()
        with scratch() as directory:
            store = RunStore(directory)
            provider = V3Provider(store)
            result = run_writing_v3(store, provider, {}, blueprint,
                                    {"name": "Ada", "location": "Berlin", "phone": "1"})
            self.assertEqual(len(provider.create_calls), 1)
            self.assertEqual(set(provider.create_calls[0]["writable_ids"]),
                             {item.id for item in blueprint.envelopes})
            self.assertEqual(result["status"], "READY")
            self.assertGreater(len(result["layout"]["selected_ids"]), 8)

    def test_saved_pending_writer_response_resumes_without_new_creation_call(self):
        from harness.generation import _prepare_v3_records, run_writing_v3
        from harness.store import RunStore
        blueprint = make_blueprint()
        with scratch() as directory:
            store = RunStore(directory)
            seeding = V3Provider(store)
            records = _prepare_v3_records(store, seeding, blueprint)
            ids = [item.id for item in blueprint.envelopes]
            response = seeding.create("", {"writable_ids": ids})
            for item_id in ids:
                records[item_id]["attempt_count"] = 1
            store.state["v3_pending_writer"] = {"ids": ids, "payload_hash": "saved", "response": response}
            store.save()
            provider = V3Provider(store, forbid_create=True)
            result = run_writing_v3(store, provider, {}, blueprint,
                                    {"name": "Ada", "location": "Berlin", "phone": "1"})
            self.assertEqual(provider.create_calls, [])
            self.assertEqual(result["status"], "READY")
            self.assertNotIn("v3_pending_writer", store.state)


if __name__ == "__main__":
    unittest.main()
