import unittest

from harness.records import SkillGroup, SkillItem, SkillKind
from test_planning_v3 import twelve_candidate_case


class DecisionProvider:
    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        self.calls = []

    def decide(self, state, questions):
        self.calls.append((state, questions))
        result = {}
        for case_id, question in questions.items():
            choice = self.overrides.get(case_id, next(iter(question["criteria"])))
            result[case_id] = {
                "choice": choice,
                "probabilities": {key: float(key == choice) for key in question["criteria"]},
                "confidence": 1.0,
            }
        return result


def blueprint_case(no_support=False):
    from harness.planning_v3 import build_blueprint
    canonical, job, decisions = twelve_candidate_case()
    if no_support:
        for key in list(decisions):
            if key.startswith("coverage__"):
                decisions[key] = "NO_SUPPORT"
    skill = SkillItem(id="s1", exact_term="Python", jd_quote="Python", kind=SkillKind.LANGUAGE,
                      display_group="Languages & interfaces", centrality="CORE", display_text="Python")
    group = SkillGroup(id="g1", label="Languages & interfaces", item_ids=["s1"])
    blueprint = build_blueprint(canonical, job, [skill], [group], decisions)
    texts = {envelope.id: f"Clear distinct text for {envelope.id}." for envelope in blueprint.envelopes}
    return blueprint, texts


class HierarchyTests(unittest.TestCase):
    def test_skill_child_fail_cannot_be_erased_by_skills_parent_pass(self):
        from harness.assessment_v3 import assess_v3, required_checks_pass
        blueprint, texts = blueprint_case()
        report = assess_v3(DecisionProvider({"s1__relevance": "FAIL"}), {}, blueprint, texts,
                           [candidate.id for candidate in blueprint.candidates])
        self.assertEqual(report.parents["skills__complete"]["choice"], "PASS")
        self.assertFalse(report.leaves["s1__relevance"]["accepted"])
        self.assertFalse(required_checks_pass(report))

    def test_bullet_fail_cannot_be_erased_by_employer_or_experience_pass(self):
        from harness.assessment_v3 import assess_v3, required_checks_pass
        blueprint, texts = blueprint_case()
        bullet_id = next(item.id for item in blueprint.envelopes if item.kind == "experience_bullet")
        report = assess_v3(DecisionProvider({f"{bullet_id}__clarity": "FAIL"}), {}, blueprint, texts,
                           [candidate.id for candidate in blueprint.candidates])
        employer_id = next(item.parent_id for item in blueprint.envelopes if item.id == bullet_id)
        self.assertEqual(report.parents[f"{employer_id}__breadth"]["choice"], "PASS")
        self.assertFalse(required_checks_pass(report))

    def test_required_uncertain_remains_unresolved(self):
        from harness.assessment_v3 import assess_v3
        blueprint, texts = blueprint_case()
        report = assess_v3(DecisionProvider({"s1__type": "UNCERTAIN"}), {}, blueprint, texts,
                           [candidate.id for candidate in blueprint.candidates])
        self.assertIn("s1__type", report.unresolved)
        self.assertFalse(report.passed)

    def test_parent_context_contains_actual_children_and_child_decisions(self):
        from harness.assessment_v3 import leaf_cases, parent_cases
        blueprint, texts = blueprint_case()
        leaves = leaf_cases(blueprint, texts)
        leaf_answers = {case.id: {"choice": "PASS"} for case in leaves}
        parents = parent_cases(blueprint, texts, [candidate.id for candidate in blueprint.candidates], leaf_answers)
        employer_case = next(case for case in parents if case.dimension == "breadth" and case.node_id.startswith("employer."))
        self.assertTrue(employer_case.state["children"])
        self.assertTrue(employer_case.state["child_decisions"])
        child_ids = {child["id"] for child in employer_case.state["children"]}
        self.assertEqual(child_ids, set(employer_case.state["dependency_ids"]))

    def test_relationship_policy_checks_letter_repetition_but_allows_cross_section_reinforcement(self):
        from harness.assessment_v3 import relationship_cases
        blueprint, texts = blueprint_case()
        cases = relationship_cases(blueprint, texts)
        self.assertTrue(any(case.node_id == "cover_letter" for case in cases))
        self.assertFalse(any("summary" in case.id and "experience" in case.id for case in cases))
        self.assertFalse(any("skills" in case.id and "experience" in case.id for case in cases))

    def test_missing_core_component_blocks_even_when_every_decision_passes(self):
        from harness.assessment_v3 import assess_v3, required_checks_pass
        blueprint, texts = blueprint_case(no_support=True)
        report = assess_v3(DecisionProvider(), {}, blueprint, texts,
                           [candidate.id for candidate in blueprint.candidates])
        self.assertEqual(report.component_coverage["c1"]["status"], "Missing")
        self.assertFalse(required_checks_pass(report))

    def test_changed_bullet_invalidates_its_ancestors_but_not_other_employer(self):
        from harness.assessment_v3 import invalidated_case_ids, leaf_cases, parent_cases, relationship_cases
        blueprint, texts = blueprint_case()
        leaves = leaf_cases(blueprint, texts)
        leaf_answers = {case.id: {"choice": "PASS"} for case in leaves}
        cases = leaves + parent_cases(blueprint, texts, [candidate.id for candidate in blueprint.candidates], leaf_answers) + relationship_cases(blueprint, texts)
        bullet = next(item for item in blueprint.envelopes if item.kind == "experience_bullet")
        other = next(item for item in blueprint.envelopes if item.kind == "experience_bullet" and item.parent_id != bullet.parent_id)
        invalid = invalidated_case_ids(cases, {bullet.id})
        self.assertTrue(any(case_id.startswith(bullet.id + "__") for case_id in invalid))
        self.assertIn(f"{bullet.parent_id}__breadth", invalid)
        self.assertIn("experience__allocation", invalid)
        self.assertFalse(any(case_id.startswith(other.id + "__") for case_id in invalid))


if __name__ == "__main__":
    unittest.main()
