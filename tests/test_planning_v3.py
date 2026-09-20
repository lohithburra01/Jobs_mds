import copy
import unittest
from collections import Counter

from harness.canonical import validate_canonical_v3
from harness.records import Component, JobV3, RequirementV3, SkillGroup, SkillItem, SkillKind
from v3_support import make_canonical_v3_fixture


def twelve_candidate_case(extra_first_employer=0):
    base = make_canonical_v3_fixture()
    template = copy.deepcopy(base["employers"][0])
    base["employers"] = []
    base["facts"] = []
    base["metrics"] = []
    base["boundaries"] = []
    line = 1
    for employer_index in range(4):
        employer_id = f"employer-{employer_index + 1}"
        boundary_id = f"{employer_id}.boundary"
        base["boundaries"].append({
            "id": boundary_id, "scope_ids": [employer_id], "text": "Keep scope accurate.",
            "source_refs": [{"archive_sha256": "a" * 64, "start_line": line, "end_line": line, "quote": "Built system one."}],
        })
        count = 3 + (extra_first_employer if employer_index == 0 else 0)
        systems = []
        for system_index in range(count):
            system_id = f"{employer_id}.system-{system_index + 1}"
            fact_id = f"{system_id}.action"
            base["facts"].append({
                "id": fact_id, "employer_id": employer_id, "system_id": system_id,
                "kind": "action", "text": f"Built distinct system {system_index + 1}.",
                "source_refs": [{"archive_sha256": "a" * 64, "start_line": line, "end_line": line, "quote": "Built system one."}],
            })
            systems.append({
                "id": system_id, "narrative": f"System {system_index + 1}",
                "source_refs": [{"archive_sha256": "a" * 64, "start_line": line, "end_line": line, "quote": "Built system one."}],
                "problem_fact_ids": [], "input_fact_ids": [], "action_fact_ids": [fact_id],
                "output_fact_ids": [], "outcome_fact_ids": [], "metric_ids": [],
                "boundary_ids": [boundary_id], "status_fact_ids": [],
                "accomplishments": [{
                    "id": f"{system_id}.accomplishment", "system_id": system_id,
                    "purpose": f"Show distinct result {system_index + 1}", "fact_ids": [fact_id],
                    "metric_ids": [], "boundary_ids": [boundary_id],
                }],
            })
        employer = copy.deepcopy(template)
        employer.update({"id": employer_id, "company": f"Company {employer_index + 1}",
                         "titles": ["Engineer"], "period": str(2026 - employer_index),
                         "boundary_ids": [boundary_id], "systems": systems})
        base["employers"].append(employer)
    canonical = validate_canonical_v3(base)
    requirement = RequirementV3(id="r1", text="Build systems", quote="Build systems", priority="CORE", component_ids=["c1"])
    component = Component(id="c1", requirement_id="r1", text="Build systems", quote="Build systems", priority="CORE")
    job = JobV3(company="Acme", role="AI Engineer", location="", thesis="Build systems",
                requirements=[requirement], components=[component], stack_items=[])
    decisions = {}
    for employer in canonical.employers:
        for system in employer.systems:
            accomplishment = system.accomplishments[0]
            decisions[f"coverage__{accomplishment.id}__c1"] = "DIRECT"
            decisions[f"relevance__{accomplishment.id}"] = "CENTRAL"
            decisions[f"specificity__{accomplishment.id}"] = "CONCRETE_OUTCOME"
    return canonical, job, decisions


class BlueprintTests(unittest.TestCase):
    def test_twelve_distinct_candidates_are_not_cut_to_eight(self):
        from harness.planning_v3 import build_blueprint
        canonical, job, decisions = twelve_candidate_case()
        blueprint = build_blueprint(canonical, job, [], [], decisions)
        self.assertEqual(len(blueprint.candidates), 12)
        counts = Counter(item.employer_id for item in blueprint.candidates)
        self.assertTrue(all(count == 3 for count in counts.values()))
        self.assertGreater(len(blueprint.candidates), 8)

    def test_employer_with_six_eligible_candidates_stops_at_four_only_for_that_employer(self):
        from harness.planning_v3 import build_blueprint
        canonical, job, decisions = twelve_candidate_case(extra_first_employer=3)
        blueprint = build_blueprint(canonical, job, [], [], decisions)
        counts = Counter(item.employer_id for item in blueprint.candidates)
        self.assertEqual(counts["employer-1"], 4)
        self.assertEqual(sum(counts.values()), 13)

    def test_relevant_old_employer_can_receive_four(self):
        from harness.planning_v3 import build_blueprint
        canonical, job, decisions = twelve_candidate_case(extra_first_employer=1)
        old_id = canonical.employers[-1].id
        # Give the oldest employer a fourth distinct accomplishment.
        source = copy.deepcopy(canonical.employers[-1].systems[0])
        source.id = old_id + ".system-4"
        source.accomplishments[0].id = source.id + ".accomplishment"
        source.accomplishments[0].system_id = source.id
        # Use the first system's fact through an explicit same-system rewrite for this isolated fixture.
        fact = copy.deepcopy(canonical.facts[-1])
        fact.id = source.id + ".action"
        fact.system_id = source.id
        source.action_fact_ids = [fact.id]
        source.accomplishments[0].fact_ids = [fact.id]
        canonical.facts.append(fact)
        canonical.employers[-1].systems.append(source)
        aid = source.accomplishments[0].id
        decisions[f"coverage__{aid}__c1"] = "DIRECT"
        decisions[f"relevance__{aid}"] = "CENTRAL"
        decisions[f"specificity__{aid}"] = "CONCRETE_OUTCOME"
        blueprint = build_blueprint(canonical, job, [], [], decisions)
        self.assertEqual(Counter(item.employer_id for item in blueprint.candidates)[old_id], 4)

    def test_redundant_alias_of_same_achievement_does_not_take_second_slot(self):
        from harness.planning_v3 import build_blueprint
        canonical, job, decisions = twelve_candidate_case()
        first_two = [system.accomplishments[0].id for system in canonical.employers[0].systems[:2]]
        decisions[f"relationship__{first_two[0]}__{first_two[1]}"] = "REDUNDANT"
        blueprint = build_blueprint(canonical, job, [], [], decisions)
        selected = {item.id for item in blueprint.candidates}
        self.assertEqual(len(selected.intersection(first_two)), 1)

    def test_project_is_local_and_has_no_employer_metric_date_or_url(self):
        from harness.planning_v3 import build_blueprint
        canonical, job, decisions = twelve_candidate_case()
        skill = SkillItem(id="s1", exact_term="LangGraph", jd_quote="LangGraph", kind=SkillKind.FRAMEWORK_LIBRARY,
                          display_group="AI frameworks & providers", centrality="CORE", display_text="LangGraph")
        group = SkillGroup(id="g1", label="AI frameworks & providers", item_ids=["s1"])
        blueprint = build_blueprint(canonical, job, [skill], [group], decisions)
        project = blueprint.prototype
        self.assertEqual(project.period, "")
        self.assertIn("LangGraph", project.target_terms)
        self.assertFalse(hasattr(project, "url"))
        self.assertFalse(project.boundary_ids)
        self.assertTrue(all(metric.id not in " ".join(project.outputs) for metric in canonical.metrics))
        self.assertTrue(any("employer metric" in item.lower() for item in project.restrictions))

    def test_writer_payload_requires_exactly_the_supplied_ids(self):
        from harness.planning_v3 import build_blueprint
        from harness.writing_v3 import validate_writer_response, writer_payload
        canonical, job, decisions = twelve_candidate_case()
        blueprint = build_blueprint(canonical, job, [], [], decisions)
        ids = [item.id for item in blueprint.envelopes]
        payload = writer_payload(blueprint, {}, ids, [])
        self.assertEqual(payload["writable_ids"], ids)
        valid = {"texts": {item_id: "Substantive text." for item_id in ids}}
        self.assertEqual(set(validate_writer_response(valid, ids)), set(ids))
        valid["texts"].pop(ids[-1])
        with self.assertRaisesRegex(ValueError, "exactly"):
            validate_writer_response(valid, ids)


if __name__ == "__main__":
    unittest.main()
