import unittest
from collections import Counter

from support import scratch
from test_planning_v3 import twelve_candidate_case


def layout_case(long=False):
    from harness.planning_v3 import build_blueprint
    canonical, job, decisions = twelve_candidate_case()
    blueprint = build_blueprint(canonical, job, [], [], decisions)
    texts = {}
    for envelope in blueprint.envelopes:
        if envelope.kind == "summary_sentence":
            texts[envelope.id] = "AI engineer building reliable production workflows."
        elif envelope.kind == "experience_bullet":
            texts[envelope.id] = ("Built and validated a distinct workflow." if not long else
                                  "Built and operated a detailed production workflow with validation, monitoring, recovery, stakeholder review, extensive documentation, and several carefully controlled integration stages across multiple business systems.")
        elif envelope.kind == "project_bullet":
            texts[envelope.id] = "Built a local workflow and validated its output."
        else:
            texts[envelope.id] = "Relevant paragraph."
    return blueprint, texts


class LayoutV3Tests(unittest.TestCase):
    def test_shared_flowables_render_more_than_eight_short_useful_bullets_on_one_page(self):
        from harness.layout_v3 import build_resume_data, measure_resume, select_fitting_experience
        blueprint, texts = layout_case()
        profile = {"name": "Ada Lovelace", "location": "Berlin", "phone": "+49 1"}
        selection = select_fitting_experience(blueprint, texts, None, profile)
        self.assertGreater(len(selection.selected_ids), 8)
        self.assertTrue(selection.checks["resume_one_page"])
        resume = build_resume_data(blueprint, texts, selection.selected_ids)
        self.assertEqual(measure_resume(resume, profile)["page_count"], 1)

    def test_every_employer_and_project_survive_fit_selection(self):
        from harness.layout_v3 import build_resume_data, select_fitting_experience
        blueprint, texts = layout_case()
        profile = {"name": "Ada Lovelace", "location": "Berlin", "phone": "+49 1"}
        selection = select_fitting_experience(blueprint, texts, None, profile)
        counts = Counter(next(item.employer_id for item in blueprint.candidates if item.id == item_id)
                         for item_id in selection.selected_ids)
        self.assertEqual(set(counts), {item.employer_id for item in blueprint.candidates})
        resume = build_resume_data(blueprint, texts, selection.selected_ids)
        self.assertEqual(len(resume["projects"]), 1)
        self.assertEqual(len(resume["projects"][0]["bullets"]), 2)

    def test_mandatory_content_overflow_is_reported_without_font_shrinking(self):
        from harness.layout_v3 import select_fitting_experience
        blueprint, texts = layout_case(long=True)
        for envelope in blueprint.envelopes:
            if envelope.kind in ("summary_sentence", "project_bullet"):
                texts[envelope.id] = " ".join([texts[envelope.id]] * 20)
        profile = {"name": "Ada Lovelace", "location": "Berlin", "phone": "+49 1"}
        selection = select_fitting_experience(blueprint, texts, None, profile)
        self.assertFalse(selection.checks["resume_one_page"])
        self.assertIn("PAGE_OVERFLOW", selection.checks["issues"])
        self.assertEqual(selection.checks["minimum_body_font_pt"], 10.0)
        counts = Counter(next(item.employer_id for item in blueprint.candidates if item.id == item_id)
                         for item_id in selection.selected_ids)
        self.assertEqual(len(counts), 4)


if __name__ == "__main__":
    unittest.main()
