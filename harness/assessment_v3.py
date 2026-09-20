"""Explicit leaf, parent, relationship, and component checks for v3."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations

from .decisions import choice
from .records import AssessmentV3, Blueprint, DecisionCase, Issue


VERDICT = {"PASS": "Meets this exact check.", "FAIL": "Clearly fails this check.", "UNCERTAIN": "Cannot determine; never assume pass."}
RELATIONSHIP = {
    "DISTINCT": "Different useful points even when vocabulary overlaps.",
    "REDUNDANT": "Retells substantially the same detailed accomplishment in the same document.",
    "CONTRADICTORY": "Makes materially inconsistent claims.",
    "UNCERTAIN": "Cannot determine the relationship.",
}


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _case(case_id, node_id, dimension, state, question_text, criteria=VERDICT):
    return DecisionCase(id=case_id, node_id=node_id, dimension=dimension, state=state,
                        question=question_text, criteria=criteria,
                        dependency_hash=_hash({"state": state, "question": question_text, "criteria": criteria}))


def leaf_cases(blueprint: Blueprint, texts: dict[str, str]) -> list[DecisionCase]:
    cases = []
    group_by_item = {item_id: group for group in blueprint.skill_groups for item_id in group.item_ids}
    for item in blueprint.skills:
        state = {"item": item.model_dump(mode="json"), "job": blueprint.job.thesis,
                 "group": group_by_item.get(item.id).model_dump(mode="json") if item.id in group_by_item else None,
                 "dependency_ids": [item.id]}
        cases.extend([
            _case(f"{item.id}__type", item.id, "type", state, "Is the semantic type correct in this JD context?"),
            _case(f"{item.id}__relevance", item.id, "relevance", state, "Is this exact item relevant to the JD?"),
            _case(f"{item.id}__specificity", item.id, "specificity", state, "Is the displayed phrase suitably specific without adding an unnamed vendor?"),
            _case(f"{item.id}__group_fit", item.id, "group_fit", state, "Does this individual item fit its assigned display group?"),
        ])

    envelope_by_id = {item.id: item for item in blueprint.envelopes}
    candidate_by_envelope = {f"experience.{item.id}": item for item in blueprint.candidates}
    for envelope in blueprint.envelopes:
        text = texts.get(envelope.id, "")
        state = {"envelope": envelope.model_dump(mode="json"), "text": text,
                 "dependency_ids": [envelope.id]}
        if envelope.kind == "experience_bullet":
            candidate = candidate_by_envelope[envelope.id]
            state["candidate"] = candidate.model_dump(mode="json")
            checks = (
                ("structure", "Does the sentence show an action, technical mechanism, and supported consequence or concrete output?"),
                ("component", "Does it express only its assigned JD components within the recorded support ceiling?"),
                ("clarity", "Can a recruiter understand the point on the first read?"),
                ("scope", "Does it preserve employer, system, metric status, ownership, and boundaries? Tool retrofit is authorized."),
            )
        elif envelope.kind == "project_bullet":
            state["prototype"] = blueprint.prototype.model_dump(mode="json")
            checks = (
                ("local_scope", "Does it clearly describe independent local work without employer scale, metrics, date, or URL?"),
                ("output", "Does it state a useful local output or validation behavior?"),
                ("component", "Does it serve its assigned JD purpose with functionally placed target tools?"),
                ("clarity", "Is it plain and readable?"),
            )
        elif envelope.kind == "summary_sentence":
            checks = (
                ("positioning", "Does this sentence perform its assigned positioning role using visible evidence?"),
                ("clarity", "Does it have clear concrete meaning rather than generic claims?"),
                ("scope", "Does it preserve the candidate's legitimate professional scope?"),
            )
        elif envelope.kind == "letter_paragraph":
            checks = (
                ("role", "Does this paragraph perform its assigned opening, proof, or closing role?"),
                ("specificity", "Does it give company/role-specific reasoning or a permitted example?"),
                ("clarity", "Is it developed, direct, and readable?"),
            )
        else:
            continue
        for dimension, question_text in checks:
            cases.append(_case(f"{envelope.id}__{dimension}", envelope.id, dimension, state, question_text))
    return cases


def relationship_cases(blueprint: Blueprint, texts: dict[str, str]) -> list[DecisionCase]:
    cases = []
    experience = [item for item in blueprint.envelopes if item.kind == "experience_bullet"]
    for left, right in combinations(experience, 2):
        state = {"left": {"id": left.id, "purpose": left.purpose, "text": texts.get(left.id, "")},
                 "right": {"id": right.id, "purpose": right.purpose, "text": texts.get(right.id, "")},
                 "dependency_ids": [left.id, right.id]}
        cases.append(_case(f"relationship__{left.id}__{right.id}", "experience", "relationship", state,
                           "Do these Experience bullets present distinct work or repeat/contradict one accomplishment?", RELATIONSHIP))
    letter = [item for item in blueprint.envelopes if item.kind == "letter_paragraph"]
    for left, right in combinations(letter, 2):
        state = {"left": {"id": left.id, "role": left.role, "text": texts.get(left.id, "")},
                 "right": {"id": right.id, "role": right.role, "text": texts.get(right.id, "")},
                 "dependency_ids": [left.id, right.id]}
        cases.append(_case(f"relationship__{left.id}__{right.id}", "cover_letter", "relationship", state,
                           "Do these letter paragraphs perform distinct roles without retelling the same proof case?", RELATIONSHIP))
    return cases


def parent_cases(blueprint: Blueprint, texts: dict[str, str], selected_ids: list[str],
                 leaf_decisions: dict) -> list[DecisionCase]:
    cases = []
    item_by_id = {item.id: item for item in blueprint.skills}
    for group in blueprint.skill_groups:
        children = [item_by_id[item_id].model_dump(mode="json") for item_id in group.item_ids]
        child_decisions = {key: value for key, value in leaf_decisions.items()
                           if any(key.startswith(item_id + "__") for item_id in group.item_ids)}
        state = {"group": group.model_dump(mode="json"), "children": children,
                 "child_decisions": child_decisions, "dependency_ids": group.item_ids}
        cases.append(_case(f"{group.id}__coherence", group.id, "coherence", state,
                           "Does the label accurately describe every examined child and contain no semantic duplicate?"))
    skill_dependencies = [item.id for item in blueprint.skills]
    skill_state = {"groups": [item.model_dump(mode="json") for item in blueprint.skill_groups],
                   "items": [item.model_dump(mode="json") for item in blueprint.skills],
                   "child_decisions": {key: value for key, value in leaf_decisions.items()
                                       if key.split("__", 1)[0] in skill_dependencies},
                   "dependency_ids": skill_dependencies}
    cases.append(_case("skills__complete", "skills", "complete", skill_state,
                       "Are classified JD implementation terms complete, ordered by centrality, and free of irrelevant vendors? Child failures remain failures."))

    experience = [item for item in blueprint.envelopes if item.kind == "experience_bullet"]
    by_parent = {}
    for item in experience:
        by_parent.setdefault(item.parent_id, []).append(item)
    for parent_id, children in by_parent.items():
        child_ids = [item.id for item in children]
        child_decisions = {key: value for key, value in leaf_decisions.items()
                           if any(key.startswith(child_id + "__") for child_id in child_ids)}
        state = {"children": [{"id": item.id, "purpose": item.purpose, "text": texts.get(item.id, "")}
                              for item in children],
                 "child_decisions": child_decisions, "dependency_ids": child_ids,
                 "omitted_candidates": {key: value for key, value in blueprint.unselected_reasons.items()
                                        if key.startswith(parent_id.removeprefix("employer."))}}
        cases.extend([
            _case(f"{parent_id}__breadth", parent_id, "breadth", state,
                  "Do these actual child bullets show useful breadth for this employer's JD contribution?"),
            _case(f"{parent_id}__distinct", parent_id, "distinct", state,
                  "Do these child bullets make distinct useful points within the employer?"),
            _case(f"{parent_id}__scope", parent_id, "scope", state,
                  "Are ownership, metrics, and system scope consistent across this employer's children?"),
        ])
    experience_ids = [item.id for item in experience]
    experience_state = {"children": [{"id": item.id, "parent_id": item.parent_id, "purpose": item.purpose,
                                       "text": texts.get(item.id, "")} for item in experience],
                        "selected_candidate_ids": selected_ids,
                        "child_decisions": {key: value for key, value in leaf_decisions.items()
                                            if any(key.startswith(child_id + "__") for child_id in experience_ids)},
                        "dependency_ids": experience_ids}
    cases.extend([
        _case("experience__distinct", "experience", "distinct", experience_state,
              "Does Experience show distinct value across employers without repeating an accomplishment?"),
        _case("experience__allocation", "experience", "allocation", experience_state,
              "Does allocation retain stronger relevant work without a chronology quota or global bullet cap?"),
    ])

    for parent_id, kind, question_text in (
        ("summary", "summary_sentence", "Does the summary form a coherent professional overview without repeating a detailed achievement?"),
        (blueprint.prototype.id, "project_bullet", "Do the project bullets form a clear independent local project with direct JD purpose and a distinct angle?"),
        ("cover_letter", "letter_paragraph", "Do the three paragraphs form a developed argument with distinct opening, proof, and closing roles?"),
    ):
        children = [item for item in blueprint.envelopes if item.parent_id == parent_id and item.kind == kind]
        child_ids = [item.id for item in children]
        state = {"children": [{"id": item.id, "role": item.role, "purpose": item.purpose,
                               "text": texts.get(item.id, "")} for item in children],
                 "child_decisions": {key: value for key, value in leaf_decisions.items()
                                     if any(key.startswith(child_id + "__") for child_id in child_ids)},
                 "dependency_ids": child_ids}
        cases.append(_case(f"{parent_id}__coherence", parent_id, "coherence", state, question_text))

    all_ids = [item.id for item in blueprint.envelopes]
    application_state = {"texts": {item_id: texts.get(item_id, "") for item_id in all_ids},
                         "dependency_ids": all_ids}
    cases.extend([
        _case("application__consistency", "application", "consistency", application_state,
              "Does the final application avoid cross-section contradictions while preserving allowed reinforcement?"),
        _case("application__coverage", "application", "coverage", application_state,
              "Does the visible application represent the supported central work components?"),
    ])
    return cases


def _run_cases(provider, cases: list[DecisionCase], batch_size=40) -> dict:
    answers = {}
    store = getattr(provider, "store", None)
    cache = store.state.setdefault("v3_case_cache", {}) if store is not None else {}
    pending = []
    for case in cases:
        serialized = json.dumps(case.state, ensure_ascii=False)
        if len(serialized) > 75_000:
            raise ValueError(f"Decision case {case.id} exceeds 75000 serialized characters: {len(serialized)}")
        cached = cache.get(case.id)
        if cached and cached.get("dependency_hash") == case.dependency_hash:
            answers[case.id] = cached["answer"]
        else:
            pending.append(case)
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        questions = {case.id: choice(case.question, case.criteria) for case in batch}
        state = {"cases": {case.id: case.state for case in batch}}
        fresh = provider.decide(state, questions)
        answers.update(fresh)
        for case in batch:
            cache[case.id] = {"dependency_hash": case.dependency_hash, "answer": fresh[case.id]}
        if store is not None:
            store.save()
    return answers


def _records(cases, answers, accepted_choice):
    return {case.id: {**answers[case.id], "node_id": case.node_id, "dimension": case.dimension,
                      "dependency_hash": case.dependency_hash,
                      "accepted": answers[case.id]["choice"] == accepted_choice}
            for case in cases}


def assess_v3(provider, policy: dict, blueprint: Blueprint, texts: dict[str, str], selected_ids: list[str]) -> AssessmentV3:
    leaves_cases = leaf_cases(blueprint, texts)
    leaves_answers = _run_cases(provider, leaves_cases)
    leaves = _records(leaves_cases, leaves_answers, "PASS")
    relation_case_list = relationship_cases(blueprint, texts)
    relation_answers = _run_cases(provider, relation_case_list) if relation_case_list else {}
    relationships = _records(relation_case_list, relation_answers, "DISTINCT")
    parents_case_list = parent_cases(blueprint, texts, selected_ids, leaves)
    parent_answers = _run_cases(provider, parents_case_list)
    parents = _records(parents_case_list, parent_answers, "PASS")

    selected = {item.id: item for item in blueprint.candidates if item.id in selected_ids}
    expressed_envelopes = {item.id: f"experience.{item.id}" for item in selected.values()}
    component_coverage = {}
    for component in blueprint.job.components:
        statuses = [(candidate.id, candidate.component_support.get(component.id, "NO_SUPPORT"))
                    for candidate in selected.values()]
        statuses.append((blueprint.prototype.id, blueprint.prototype.component_support.get(component.id, "NO_SUPPORT")))
        direct = [expressed_envelopes.get(item_id, item_id) for item_id, status in statuses if status == "DIRECT"]
        partial = [expressed_envelopes.get(item_id, item_id) for item_id, status in statuses if status in ("PARTIAL", "ADJACENT")]
        uncertain = [expressed_envelopes.get(item_id, item_id) for item_id, status in statuses if status == "UNCERTAIN"]
        if direct:
            status, expressed = "Explicit", direct
        elif partial:
            status, expressed = "Partial", partial
        elif uncertain:
            status, expressed = "Uncertain", uncertain
        else:
            status, expressed = "Missing", []
        component_coverage[component.id] = {"priority": component.priority, "status": status,
                                             "expressed_ids": expressed, "quote": component.quote}

    issues = []
    unresolved = []
    for collection_name, collection in (("LEAF", leaves), ("PARENT", parents), ("RELATIONSHIP", relationships)):
        for case_id, record in collection.items():
            if record["accepted"]:
                continue
            issues.append(Issue(code=f"{collection_name}_FAILED", node_ids=[record["node_id"]],
                                target_ids=[record["node_id"]] if collection_name == "LEAF" else [],
                                instruction=f"Resolve {case_id}: {record['choice']}.", decision_ids=[case_id],
                                unresolved=record["choice"] == "UNCERTAIN" or collection_name != "LEAF"))
            if record["choice"] == "UNCERTAIN" or collection_name != "LEAF":
                unresolved.append(case_id)
    for component_id, coverage in component_coverage.items():
        if coverage["priority"] == "CORE" and coverage["status"] != "Explicit":
            issues.append(Issue(code="CORE_COMPONENT_INCOMPLETE", node_ids=[component_id],
                                instruction=f"Core component {component_id} is {coverage['status']}.",
                                unresolved=True))
            unresolved.append(component_id)
    report = AssessmentV3(
        leaves=leaves, parents=parents, component_coverage=component_coverage,
        relationships=relationships, issues=issues, unresolved=sorted(set(unresolved)),
        text_hashes={item_id: _hash(text) for item_id, text in texts.items()},
        selected_ids=selected_ids, passed=False,
    )
    report.passed = required_checks_pass(report)
    return report


def required_checks_pass(report: AssessmentV3) -> bool:
    if report.unresolved:
        return False
    if any(not record.get("accepted", False) for record in report.leaves.values()):
        return False
    if any(not record.get("accepted", False) for record in report.parents.values()):
        return False
    if any(not record.get("accepted", False) for record in report.relationships.values()):
        return False
    return all(value.get("status") == "Explicit" for value in report.component_coverage.values()
               if value.get("priority") == "CORE")


def invalidated_case_ids(cases: list[DecisionCase], changed_node_ids: set[str]) -> set[str]:
    invalid = set()
    for case in cases:
        dependencies = set(case.state.get("dependency_ids", []))
        if case.node_id in changed_node_ids or dependencies.intersection(changed_node_ids):
            invalid.add(case.id)
    return invalid
