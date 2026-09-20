import unittest

from harness.records import Component, JobV3, RequirementV3, SkillItem, SkillKind
from support import scratch


class FixedProvider:
    def __init__(self, draft=None, overrides=None):
        self.draft = draft
        self.overrides = overrides or {}
        self.create_calls = []
        self.decide_calls = []

    def create(self, instructions, payload):
        self.create_calls.append((instructions, payload))
        return self.draft

    def decide(self, state, questions):
        self.decide_calls.append((state, questions))
        answers = {}
        for question_id, question in questions.items():
            choice = self.overrides.get(question_id)
            if choice is None:
                choice = next(iter(question["criteria"]))
            answers[question_id] = {
                "choice": choice,
                "probabilities": {item: float(item == choice) for item in question["criteria"]},
                "confidence": 1.0,
            }
        return answers


def make_job(terms):
    requirement = RequirementV3(
        id="r1", text="Build the implementation", quote="Build the implementation", priority="CORE",
        component_ids=["c1"],
    )
    component = Component(
        id="c1", requirement_id="r1", text="Build the implementation",
        quote="Build the implementation", priority="CORE",
    )
    items = [
        SkillItem(id=f"s{i}", exact_term=term, jd_quote=term, kind=SkillKind.UNCERTAIN,
                  display_group="", centrality="UNCERTAIN", display_text=term)
        for i, term in enumerate(terms, 1)
    ]
    return JobV3(company="Acme", role="Engineer", location="", thesis="Build it", requirements=[requirement], components=[component], stack_items=items)


class JobStructureTests(unittest.TestCase):
    def test_composite_requirement_keeps_deployment_integration_and_controls(self):
        from harness.skills import analyze_job_v3
        jd = "Deploy production AI applications, integrate them with enterprise APIs, and add monitoring, retries, and recovery controls."
        provider = FixedProvider({
            "company": "Acme", "role": "AI Engineer", "location": "", "thesis": "Production AI delivery",
            "requirements": [{
                "text": "Deploy reliable production AI applications",
                "quote": jd,
                "components": [
                    {"text": "Deploy production AI applications", "quote": "Deploy production AI applications"},
                    {"text": "Integrate with enterprise APIs", "quote": "integrate them with enterprise APIs"},
                    {"text": "Add monitoring, retries, and recovery controls", "quote": "monitoring, retries, and recovery controls"},
                ],
            }],
            "stack": [{"exact_term": "APIs", "quote": "enterprise APIs"}],
        })
        with scratch() as directory:
            from harness.store import RunStore
            job = analyze_job_v3(RunStore(directory), provider, {"priority": {"CORE": "central"}, "verdict": {"PASS": "yes", "FAIL": "no", "UNCERTAIN": "unclear"}}, jd)
        self.assertEqual(len(job.components), 3)
        self.assertEqual({item.text for item in job.components}, {
            "Deploy production AI applications", "Integrate with enterprise APIs",
            "Add monitoring, retries, and recovery controls",
        })
        self.assertTrue(all(item.quote in jd for item in job.components))


class SkillClassificationTests(unittest.TestCase):
    TERMS = ["OpenAI", "LangChain", "Python", "Docker", "CI/CD", "MLOps", "AI", "LLMs", "vector databases"]

    def provider(self, extra=None):
        kinds = {
            "OpenAI": "PROVIDER", "LangChain": "FRAMEWORK_LIBRARY", "Python": "LANGUAGE",
            "Docker": "DEPLOYMENT_TOOL", "CI/CD": "METHOD_ARCHITECTURE", "MLOps": "METHOD_ARCHITECTURE",
            "AI": "DOMAIN", "LLMs": "UNSPECIFIED_FAMILY", "vector databases": "UNSPECIFIED_FAMILY",
        }
        overrides = {}
        for index, term in enumerate(self.TERMS, 1):
            overrides[f"s{index}__kind"] = kinds[term]
            overrides[f"s{index}__relevance"] = "RELEVANT"
            overrides[f"s{index}__specificity"] = "SUITABLE"
            overrides[f"s{index}__centrality"] = "CORE" if index < 5 else "SUPPORTING"
        overrides.update(extra or {})
        return FixedProvider(overrides=overrides)

    def test_each_item_gets_its_own_kind_and_permitted_group(self):
        from harness.skills import ALLOWED_GROUPS_BY_KIND, classify_skills
        job = make_job(self.TERMS)
        items, groups, issues = classify_skills(self.provider(), {}, job)
        by_term = {item.exact_term: item for item in items}
        self.assertEqual(by_term["OpenAI"].kind.value, "PROVIDER")
        self.assertEqual(by_term["LangChain"].kind.value, "FRAMEWORK_LIBRARY")
        self.assertEqual(by_term["Python"].kind.value, "LANGUAGE")
        self.assertEqual(by_term["Docker"].kind.value, "DEPLOYMENT_TOOL")
        self.assertEqual(by_term["CI/CD"].kind.value, "METHOD_ARCHITECTURE")
        self.assertEqual(by_term["MLOps"].kind.value, "METHOD_ARCHITECTURE")
        self.assertEqual(by_term["AI"].kind.value, "DOMAIN")
        self.assertEqual(by_term["LLMs"].kind.value, "UNSPECIFIED_FAMILY")
        for item in items:
            if item.kind not in (SkillKind.DOMAIN, SkillKind.UNCERTAIN):
                self.assertIn(item.display_group, ALLOWED_GROUPS_BY_KIND[item.kind])
        self.assertFalse([issue for issue in issues if issue.code == "SKILL_UNRESOLVED"])
        self.assertTrue(groups)

    def test_all_non_domain_terms_survive_without_invented_vendor(self):
        from harness.skills import classify_skills
        items, groups, _ = classify_skills(self.provider(), {}, make_job(self.TERMS))
        displayed = " | ".join(item.display_text for item in items if item.kind != SkillKind.DOMAIN)
        for term in set(self.TERMS) - {"AI"}:
            self.assertIn(term, displayed)
        self.assertNotIn("Pinecone", displayed)
        self.assertIn("LLM integration (LLMs)", displayed)
        self.assertTrue(any(item.exact_term == "AI" and item.kind == SkillKind.DOMAIN for item in items))
        grouped_ids = {item_id for group in groups for item_id in group.item_ids}
        self.assertNotIn(next(item.id for item in items if item.exact_term == "AI"), grouped_ids)

    def test_group_pass_does_not_hide_failed_child(self):
        from harness.skills import classify_skills
        provider = self.provider({"s3__relevance": "IRRELEVANT"})
        items, groups, issues = classify_skills(provider, {}, make_job(self.TERMS))
        python_id = next(item.id for item in items if item.exact_term == "Python")
        self.assertTrue(groups)
        self.assertTrue(any(issue.code == "SKILL_ITEM_FAILED" and python_id in issue.node_ids for issue in issues))


if __name__ == "__main__":
    unittest.main()
