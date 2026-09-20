"""Deterministic v3 candidate selection after Jev supplies semantic decisions."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations

from .records import (
    Blueprint, Candidate, CanonicalV3, DecisionCase, Envelope, JobV3,
    Prototype, SkillGroup, SkillItem, SkillKind,
)


COVERAGE = {
    "DIRECT": "Substantially the same work; tool differences are ignored.",
    "PARTIAL": "Some but not all of the work is demonstrated.",
    "ADJACENT": "Related transferable engineering work.",
    "NO_SUPPORT": "This accomplishment does not support the component.",
    "UNCERTAIN": "Support cannot be determined.",
}
RELEVANCE = {
    "CENTRAL": "Central evidence for this JD.",
    "SUPPORTING": "Useful supporting evidence.",
    "INCIDENTAL": "Little value for this JD.",
    "UNCERTAIN": "Relevance cannot be determined.",
}
SPECIFICITY = {
    "CONCRETE_OUTCOME": "Specific result, scale, or operational consequence.",
    "CONCRETE_WORK": "Specific implemented artifact or action.",
    "GENERAL": "Broad capability description.",
    "UNCERTAIN": "Specificity cannot be determined.",
}
RELATIONSHIP = {
    "DISTINCT": "Different useful accomplishment.",
    "REDUNDANT": "Same accomplishment or consequence under another label.",
    "CONTRADICTORY": "Cannot appear together accurately.",
    "UNCERTAIN": "Relationship cannot be determined.",
}


def _answer(decisions: dict, key: str, default: str) -> str:
    value = decisions.get(key, default)
    return value.get("choice", default) if isinstance(value, dict) else value


def _case(case_id: str, node_id: str, dimension: str, state: dict, question: str, criteria: dict[str, str]) -> DecisionCase:
    dependency_hash = hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return DecisionCase(id=case_id, node_id=node_id, dimension=dimension, state=state,
                        question=question, criteria=criteria, dependency_hash=dependency_hash)


def planning_cases(canonical: CanonicalV3, job: JobV3) -> list[DecisionCase]:
    cases = []
    accomplishments = []
    for employer in canonical.employers:
        for system in employer.systems:
            for accomplishment in system.accomplishments:
                state = {
                    "employer_id": employer.id,
                    "system": system.model_dump(mode="json"),
                    "accomplishment": accomplishment.model_dump(mode="json"),
                }
                accomplishments.append((employer.id, accomplishment.id, state))
                for component in job.components:
                    cstate = {**state, "component": component.model_dump(mode="json")}
                    cases.append(_case(
                        f"coverage__{accomplishment.id}__{component.id}", accomplishment.id,
                        "component_support", cstate,
                        "How directly does only this same-system accomplishment support this JD work component? Historical tool names do not affect support.",
                        COVERAGE,
                    ))
                cases.append(_case(f"relevance__{accomplishment.id}", accomplishment.id, "relevance", state,
                                   "How central is this accomplishment to the JD's work?", RELEVANCE))
                cases.append(_case(f"specificity__{accomplishment.id}", accomplishment.id, "specificity", state,
                                   "How concrete is this recorded accomplishment?", SPECIFICITY))
    by_employer = {}
    for employer_id, accomplishment_id, state in accomplishments:
        by_employer.setdefault(employer_id, []).append((accomplishment_id, state))
    for employer_items in by_employer.values():
        for (left, left_state), (right, right_state) in combinations(employer_items, 2):
            state = {"left": left_state, "right": right_state}
            cases.append(_case(f"relationship__{left}__{right}", left, "relationship", state,
                               "Are these distinct accomplishments or aliases/repetitions of the same achievement?", RELATIONSHIP))
    return cases


def _candidate_score(candidate: Candidate, components: dict[str, object]) -> tuple:
    direct_core = sum(1 for cid, status in candidate.component_support.items()
                      if status == "DIRECT" and components[cid].priority == "CORE")
    partial_core = sum(1 for cid, status in candidate.component_support.items()
                       if status == "PARTIAL" and components[cid].priority == "CORE")
    direct_supporting = sum(1 for cid, status in candidate.component_support.items()
                            if status == "DIRECT" and components[cid].priority == "SUPPORTING")
    relevance = {"CENTRAL": 3, "SUPPORTING": 2, "INCIDENTAL": 1, "UNCERTAIN": 0}.get(candidate.relevance, 0)
    specificity = {"CONCRETE_OUTCOME": 3, "CONCRETE_WORK": 2, "GENERAL": 1, "UNCERTAIN": 0}.get(candidate.specificity, 0)
    return direct_core, partial_core, direct_supporting, relevance, specificity


def build_blueprint(canonical: CanonicalV3, job: JobV3, skills: list[SkillItem],
                    groups: list[SkillGroup], decisions: dict) -> Blueprint:
    facts = {item.id: item for item in canonical.facts}
    components = {item.id: item for item in job.components}
    implementation_terms = [item.exact_term for item in skills
                            if item.kind not in (SkillKind.DOMAIN, SkillKind.UNCERTAIN)
                            and item.centrality in ("CORE", "SUPPORTING")]
    selected = []
    unselected = {}
    for employer in canonical.employers:
        candidates = []
        for system in employer.systems:
            for accomplishment in system.accomplishments:
                support = {component.id: _answer(decisions, f"coverage__{accomplishment.id}__{component.id}", "NO_SUPPORT")
                           for component in job.components}
                supported = [cid for cid, status in support.items() if status in ("DIRECT", "PARTIAL", "ADJACENT")]
                primary = sorted(supported, key=lambda cid: (
                    {"CORE": 0, "SUPPORTING": 1, "PERIPHERAL": 2, "UNCERTAIN": 3}.get(components[cid].priority, 3),
                    {"DIRECT": 0, "PARTIAL": 1, "ADJACENT": 2}.get(support[cid], 3), cid,
                ))[0] if supported else ""
                target_terms = [term for term in implementation_terms
                                if _answer(decisions, f"placement__{accomplishment.id}__{term}", "FUNCTIONAL") == "FUNCTIONAL"][:3]
                candidates.append(Candidate(
                    id=accomplishment.id, employer_id=employer.id, system_id=system.id,
                    purpose=accomplishment.purpose, fact_ids=accomplishment.fact_ids,
                    metric_ids=accomplishment.metric_ids, boundary_ids=accomplishment.boundary_ids,
                    component_support=support, primary_component_id=primary, target_terms=target_terms,
                    relevance=_answer(decisions, f"relevance__{accomplishment.id}", "INCIDENTAL"),
                    specificity=_answer(decisions, f"specificity__{accomplishment.id}", "GENERAL"),
                    contextual_only=not supported,
                ))
        candidates.sort(key=lambda candidate: tuple(-value for value in _candidate_score(candidate, components)) + (candidate.id,))
        employer_selected = []
        for candidate in candidates:
            if len(employer_selected) == canonical.policies.max_bullets_per_employer:
                unselected[candidate.id] = "employer maximum of four stronger distinct candidates"
                continue
            redundant = False
            for earlier in employer_selected:
                forward = f"relationship__{earlier.id}__{candidate.id}"
                reverse = f"relationship__{candidate.id}__{earlier.id}"
                relationship = _answer(decisions, forward, _answer(decisions, reverse, "DISTINCT"))
                if relationship in ("REDUNDANT", "CONTRADICTORY"):
                    unselected[candidate.id] = f"{relationship.lower()} with {earlier.id}"
                    redundant = True
                    break
            if not redundant and (not candidate.contextual_only or not employer_selected):
                employer_selected.append(candidate)
            elif not redundant:
                unselected[candidate.id] = "contextual candidate weaker than selected work"
        if not employer_selected and candidates:
            fallback = candidates[0].model_copy(update={"contextual_only": True})
            employer_selected.append(fallback)
            unselected.pop(fallback.id, None)
        selected.extend(employer_selected)

    if len({candidate.employer_id for candidate in selected}) != len(canonical.employers):
        raise ValueError("Blueprint must retain at least one candidate for every employer")
    source_candidate = next((item for item in selected if not item.contextual_only), selected[0])
    prototype_support = {component.id: ("DIRECT" if component.id == source_candidate.primary_component_id else "PARTIAL"
                                         if source_candidate.component_support.get(component.id) == "PARTIAL" else "NO_SUPPORT")
                         for component in job.components}
    prototype = Prototype(
        id="project.local-prototype", name=f"Local {job.role} Workflow Prototype", period="",
        pattern_id="canonical.prototype_pattern", source_system_id=source_candidate.system_id,
        local_steps=[
            "Define representative local inputs and an explicit end-to-end workflow contract.",
            "Implement the workflow with the JD's central stack and deterministic validation around model behavior.",
            "Run the small-scale workflow locally, inspect the output, and publish the implementation to GitHub.",
        ],
        outputs=[f"A working local proof of the {job.thesis.lower()} workflow with inspectable output."],
        target_terms=implementation_terms, component_support=prototype_support, boundary_ids=[],
        restrictions=canonical.prototype_pattern.restrictions,
    )

    envelopes = [
        Envelope(id=f"summary.{index}", kind="summary_sentence", parent_id="summary", role=role,
                 purpose=purpose, component_ids=[item.id for item in job.components if item.priority == "CORE"],
                 target_terms=implementation_terms[:5], writing_guidance="One substantive sentence; the complete summary should normally total roughly 55-80 words.")
        for index, (role, purpose) in enumerate((
            ("identity", "State the role-relevant professional identity and breadth."),
            ("work", "Explain the central kinds of systems and operational problems solved."),
            ("stack", "Connect the central implementation stack to the demonstrated workflow patterns."),
        ), 1)
    ]
    for candidate in selected:
        envelopes.append(Envelope(
            id=f"experience.{candidate.id}", kind="experience_bullet", parent_id=f"employer.{candidate.employer_id}",
            role="accomplishment", purpose=candidate.purpose, source_fact_ids=candidate.fact_ids,
            source_metric_ids=candidate.metric_ids, boundary_ids=candidate.boundary_ids,
            component_ids=[cid for cid, status in candidate.component_support.items() if status != "NO_SUPPORT"],
            target_terms=candidate.target_terms,
            writing_guidance="Explain one useful action, technical mechanism, and consequence; roughly 20-40 words is guidance only.",
        ))
    for index, purpose in enumerate(("Explain the local problem, input, and JD-stack workflow.",
                                     "Explain the concrete local output and validation behavior."), 1):
        envelopes.append(Envelope(
            id=f"project.{index}", kind="project_bullet", parent_id=prototype.id, role="prototype",
            purpose=purpose, component_ids=[cid for cid, value in prototype.component_support.items() if value != "NO_SUPPORT"],
            target_terms=prototype.target_terms, writing_guidance="Concise local-project bullet; no employer scale, metric, date, or URL.",
        ))
    for index, (role, purpose) in enumerate((
        ("opening", "Connect this particular company and role to the candidate's relevant breadth."),
        ("proof", "Develop one strong example that demonstrates the central work."),
        ("closing", "State a specific prospective contribution and close directly."),
    ), 1):
        envelopes.append(Envelope(
            id=f"letter.{index}", kind="letter_paragraph", parent_id="cover_letter", role=role,
            purpose=purpose, component_ids=[item.id for item in job.components if item.priority == "CORE"],
            target_terms=implementation_terms, writing_guidance="Developed paragraph; all three paragraphs normally total roughly 220-300 words.",
        ))

    fixed_fields = {
        "profile": canonical.profile,
        "education": [item.model_dump(mode="json") for item in canonical.education],
        "employers": [{"id": item.id, "company": item.company, "titles": item.titles, "period": item.period}
                      for item in canonical.employers],
        "identity": canonical.identity,
    }
    return Blueprint(job=job, skills=skills, skill_groups=groups, candidates=selected,
                     prototype=prototype, envelopes=envelopes, fixed_fields=fixed_fields,
                     unselected_reasons=unselected)
