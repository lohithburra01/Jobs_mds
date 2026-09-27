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


POLICY = {"priority": {"CORE": "central"}, "verdict": {"PASS": "yes", "FAIL": "no", "UNCERTAIN": "unclear"}}
BRIEF = {"summary": "AI engineer who ships production AI services.", "must_haves": ["Production AI delivery"], "nice_to_haves": []}


def draft(requirements, stack=None, brief=None):
    return {"company": "Acme", "role": "AI Engineer", "location": "", "thesis": "Production AI",
            "brief": brief or BRIEF, "requirements": requirements, "stack": stack or []}


class JobStructureTests(unittest.TestCase):
    def analyze(self, provider, jd):
        from harness.skills import analyze_job_v3
        from harness.store import RunStore
        with scratch() as directory:
            job = analyze_job_v3(RunStore(directory), provider, POLICY, jd)
            note = (directory / "role-brief.md").read_text(encoding="utf-8")
        return job, note

    def test_jd_decisions_are_sent_in_bounded_batches(self):
        passages = [f"Requirement {index} deploys service {index} with monitoring." for index in range(1, 16)]

        class BoundedProvider(FixedProvider):
            def decide(self, state, questions):
                if len(questions) > 40:
                    raise AssertionError(f"oversized Jev batch: {len(questions)}")
                return super().decide(state, questions)

        provider = BoundedProvider(draft([{"text": p, "quote": p, "components": [{"text": p, "quote": p}]} for p in passages]))
        job, _ = self.analyze(provider, "\n".join(passages))
        self.assertEqual(len(job.requirements), 15)
        self.assertGreater(len(provider.decide_calls), 1)
        self.assertTrue(all(len(questions) <= 40 for _, questions in provider.decide_calls))

    def test_composite_requirement_keeps_deployment_integration_and_controls(self):
        jd = "Deploy production AI applications, integrate them with enterprise APIs, and add monitoring, retries, and recovery controls."
        provider = FixedProvider(draft([{
            "text": "Deploy reliable production AI applications", "quote": jd,
            "components": [
                {"text": "Deploy production AI applications", "quote": "Deploy production AI applications"},
                {"text": "Integrate with enterprise APIs", "quote": "integrate them with enterprise APIs"},
                {"text": "Add monitoring, retries, and recovery controls", "quote": "monitoring, retries, and recovery controls"},
            ]}], stack=[{"exact_term": "APIs", "quote": "enterprise APIs"}]))
        job, _ = self.analyze(provider, jd)
        self.assertEqual(len(job.components), 3)
        self.assertTrue(all(item.quote in jd for item in job.components))
        self.assertEqual(job.brief.stack, ["APIs"])

    def test_noncontiguous_component_short_quote_falls_back_to_exact_parent_passage(self):
        jd = "Design, build, and deploy AI-powered solutions, automations, and agents."
        provider = FixedProvider(draft([{"text": "Deliver AI solutions", "quote": jd,
                                         "components": [{"text": "Design AI-powered solutions", "quote": "Design AI-powered solutions"}]}]))
        job, _ = self.analyze(provider, jd)
        self.assertEqual(job.components[0].quote, jd)

    def test_missing_work_passage_is_reported_not_fatal(self):
        jd = "Build AI services. Maintain audit logs for every automated action."
        provider = FixedProvider(draft([{"text": "Build AI services", "quote": "Build AI services."}]),
                                 overrides={"passage_2__coverage": "MISSING"})
        job, note = self.analyze(provider, jd)
        self.assertEqual(len(provider.create_calls), 1)
        self.assertEqual([(item.kind, item.text) for item in job.unresolved],
                         [("PASSAGE_MISSING", "Maintain audit logs for every automated action.")])
        self.assertIn("Maintain audit logs", note)

    def test_self_contradicting_reviewer_does_not_stop_the_run(self):
        # The run-3 contradiction: company context flagged missing, and judged unfaithful once included.
        jd = "As Acme grows, we are strengthening our IT organization.\nBuild internal AI tools for business teams."
        provider = FixedProvider(draft([
            {"text": "Acme is strengthening IT", "quote": "As Acme grows, we are strengthening our IT organization."},
            {"text": "Build internal AI tools", "quote": "Build internal AI tools for business teams."},
        ]), overrides={"passage_1__label": "COMPANY_CONTEXT", "passage_1__coverage": "MISSING", "r1.c1__faithful": "FAIL"})
        job, _ = self.analyze(provider, jd)
        self.assertEqual(len(provider.create_calls), 1)
        self.assertEqual(len(job.requirements), 2)
        self.assertEqual([(item.kind, item.node_id) for item in job.unresolved], [("INTERPRETATION_FAIL", "r1.c1")])

    def test_three_line_jd_without_components_works(self):
        jd = "Python developer wanted.\nBuild data pipelines for our analysts.\nRemote, full time."
        provider = FixedProvider(draft([{"text": "Build data pipelines", "quote": "Build data pipelines for our analysts."}],
                                       stack=[{"exact_term": "Python", "quote": "Python developer wanted."}],
                                       brief={"summary": "Python developer who builds data pipelines for analysts.",
                                              "must_haves": ["Python", "Data pipelines"]}))
        job, note = self.analyze(provider, jd)
        self.assertEqual([(item.id, item.text) for item in job.components], [("r1.c1", "Build data pipelines")])
        self.assertIn("Python developer who builds data pipelines", note)

    def test_non_english_jd_keeps_original_language_quotes(self):
        jd = "Vous concevrez des agents IA pour les équipes métier.\nMaîtrise de Python exigée."
        provider = FixedProvider(draft([
            {"text": "Design AI agents for business teams", "quote": "Vous concevrez des agents IA pour les équipes métier."},
            {"text": "Python proficiency", "quote": "Maîtrise de Python exigée."},
        ], stack=[{"exact_term": "Python", "quote": "Maîtrise de Python exigée."}],
            brief={"summary": "AI engineer designing agents for business teams in Python.", "must_haves": ["AI agents", "Python"]}))
        job, _ = self.analyze(provider, jd)
        self.assertEqual(job.requirements[0].quote, "Vous concevrez des agents IA pour les équipes métier.")
        self.assertEqual(job.requirements[0].text, "Design AI agents for business teams")
        self.assertEqual(job.unresolved, [])

    def test_quote_not_in_jd_is_reported_and_skipped(self):
        jd = "Build AI services for finance teams."
        provider = FixedProvider(draft([
            {"text": "Build AI services", "quote": "Build AI services for finance teams."},
            {"text": "Invented requirement", "quote": "Manage a team of twenty."},
        ]))
        job, _ = self.analyze(provider, jd)
        self.assertEqual(len(job.requirements), 1)
        self.assertEqual([item.kind for item in job.unresolved], ["QUOTE_NOT_IN_JD"])

    def test_unusable_output_is_retried_once_then_stops_clearly(self):
        provider = FixedProvider({"company": "Acme"})
        with self.assertRaisesRegex(ValueError, "unusable output twice"):
            self.analyze(provider, "Build AI services.")
        self.assertEqual(len(provider.create_calls), 2)

    def test_personal_qualification_is_a_valid_component_kind(self):
        jd = "Highly autonomous, curious, and comfortable in a fast-moving environment"
        provider = FixedProvider(draft([{"text": "Work autonomously", "quote": jd}]))
        self.analyze(provider, jd)
        questions = provider.decide_calls[0][1]
        self.assertIn("qualification or personal requirement", questions["r1.c1__faithful"]["instructions"])



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
