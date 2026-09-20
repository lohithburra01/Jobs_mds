import unittest


def unit(uid, employer, heading, specificity="GENERAL"):
    return {"id": uid, "employer_id": employer, "heading": heading, "text": heading,
            "boundaries": "Keep facts scoped.", "specificity": specificity}


class SelectionTests(unittest.TestCase):
    def canonical(self):
        employers = [{"id": e, "company": e, "titles": ["Engineer"], "period": "2024"}
                     for e in ("a", "b", "c", "d")]
        evidence = [unit("a:aaa-general", "a", "general", "GENERAL"),
                    unit("a:zzz-outcome", "a", "outcome", "CONCRETE_OUTCOME"),
                    unit("a:other", "a", "other", "CONCRETE_WORK")]
        evidence += [unit(f"{e}:one", e, e, "CONCRETE_WORK") for e in ("b", "c", "d")]
        evidence += [unit("b:two", "b", "b two"), unit("c:two", "c", "c two")]
        return {"employers": employers, "evidence": evidence, "identity": "Engineer"}

    def test_equal_relevance_prefers_concrete_outcome(self):
        from harness.planning import select_plan
        canonical = self.canonical()
        requirements = [{"id": "r1", "text": "Build systems", "priority": "CORE"}]
        coverage = {u["id"]: {"r1": "DIRECT"} for u in canonical["evidence"]}
        plan = select_plan(canonical, requirements, coverage)
        primary = next(b for b in plan["blocks"] if b["employer_id"] == "a" and "r1" in b["requirement_ids"])
        self.assertEqual(primary["evidence"][0]["id"], "a:zzz-outcome")

    def test_higher_relevance_beats_unrelated_metric(self):
        from harness.planning import select_plan
        canonical = self.canonical()
        requirements = [{"id": "r1", "text": "Build systems", "priority": "CORE"}]
        coverage = {u["id"]: {"r1": "DIRECT"} for u in canonical["evidence"]}
        coverage["a:zzz-outcome"]["r1"] = "NO_SUPPORT"
        plan = select_plan(canonical, requirements, coverage)
        selected = [b["evidence"][0]["id"] for b in plan["blocks"] if b["employer_id"] == "a"]
        self.assertIn("a:aaa-general", selected)


class WritingPlanTests(unittest.TestCase):
    def test_each_bullet_gets_one_purpose_and_letter_roles_are_distinct(self):
        from harness.writing_plan import build_writing_plan
        requirements = [{"id": f"r{i}", "text": f"Requirement {i}",
                         "priority": "CORE" if i < 5 else "SUPPORTING"} for i in range(1, 8)]
        blocks = []
        employers = []
        for i in range(1, 9):
            employer = chr(96 + min(i, 4))
            employers.append(employer)
            evidence = unit(f"{employer}:{i}", employer, f"Evidence {i}",
                            "CONCRETE_OUTCOME" if i == 1 else "CONCRETE_WORK")
            coverage = {r["id"]: ("DIRECT" if i == 1 else "ADJACENT") for r in requirements}
            blocks.append({"id": f"{employer}_{i}", "kind": "bullet", "employer_id": employer,
                           "purpose": "; ".join(r["text"] for r in requirements),
                           "requirement_ids": list(coverage), "potential_requirement_ids": list(coverage),
                           "primary_requirement_id": "r1" if i == 1 else None,
                           "coverage": coverage, "evidence": [evidence], "target_terms": []})
        canonical = {"identity": "AI engineer", "employers": [{"id": e} for e in sorted(set(employers))]}
        job = {"requirements": requirements, "stack": [{"term": "LLMs"}], "company": "Acme", "role": "AI Engineer"}
        envelopes = build_writing_plan(canonical, job, {"blocks": blocks})
        by_id = {b["id"]: b for b in envelopes}
        resume = [b for b in envelopes if b["kind"] == "bullet"]
        self.assertEqual(len({b["id"] for b in envelopes}), len(envelopes))
        self.assertTrue(all(";" not in b["purpose"] for b in resume))
        self.assertTrue(all(len(b["potential_requirement_ids"]) == 7 for b in resume))
        self.assertEqual(len(by_id["letter_2"]["evidence"]), 1)
        self.assertEqual(by_id["letter_1"]["role"], "opening")
        self.assertEqual(by_id["letter_3"]["role"], "closing")
        self.assertTrue(all(b["max_words"] == 38 for b in resume))
        self.assertEqual(by_id["summary"]["max_words"], 60)
        self.assertEqual([by_id[f"letter_{i}"]["max_words"] for i in range(1, 4)], [60, 95, 60])


if __name__ == "__main__":
    unittest.main()
