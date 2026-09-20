"""Turn selected evidence into single-purpose writing envelopes."""
from copy import deepcopy

from .planning import SCORES, SPECIFICITY


def _specificity(block):
    return SPECIFICITY.get(block["evidence"][0].get("specificity", "UNCERTAIN"), 0)


def _proof_block(blocks, requirements):
    core = {r["id"] for r in requirements if r["priority"] == "CORE"}
    def rank(block):
        support = sum(SCORES.get(value, 0) for rid, value in block.get("coverage", {}).items() if rid in core)
        return (-support, -_specificity(block), block["evidence"][0]["id"])
    return sorted(blocks, key=rank)[0]


def build_writing_plan(canonical: dict, job: dict, plan: dict) -> list[dict]:
    """Return all resume/letter envelopes without changing the public output schema."""
    requirements = {r["id"]: r for r in job["requirements"]}
    bullets = []
    for source in plan["blocks"]:
        block = deepcopy(source)
        primary = block.get("primary_requirement_id")
        if primary not in requirements:
            potential = block.get("potential_requirement_ids", block.get("requirement_ids", []))
            primary = potential[0] if potential else None
        block["primary_requirement_id"] = primary
        block["potential_requirement_ids"] = block.get("potential_requirement_ids", block.get("requirement_ids", []))
        block["purpose"] = requirements[primary]["text"] if primary else f"Show the concrete work in {block['evidence'][0]['heading']}"
        block.update(role="experience", target_words=32, max_words=38)
        bullets.append(block)

    selected = [b["evidence"][0] for b in bullets]
    proof = _proof_block(bullets, job["requirements"])
    stack = [x["term"] for x in job.get("stack", [])]
    summary = {"id": "summary", "kind": "summary", "role": "summary",
        "purpose": "State the professional identity, problems solved, and central capabilities for this role without detailed achievements.",
        "evidence": selected, "target_terms": stack[:5], "target_words": 50, "max_words": 60,
        "primary_requirement_id": None, "potential_requirement_ids": []}
    opening = {"id": "letter_1", "kind": "letter", "role": "opening",
        "purpose": "Identify the role and connect one stated hiring need to the candidate's experience without a named-employer case study or metrics.",
        "evidence": selected, "target_terms": stack[:3], "target_words": 50, "max_words": 60,
        "primary_requirement_id": None, "potential_requirement_ids": []}
    proof_paragraph = {"id": "letter_2", "kind": "letter", "role": "proof",
        "purpose": "Explain this one reserved example, its supported impact, and why it matters for the role.",
        "evidence": deepcopy(proof["evidence"]), "target_terms": proof.get("target_terms", []),
        "target_words": 80, "max_words": 95, "primary_requirement_id": proof.get("primary_requirement_id"),
        "potential_requirement_ids": proof.get("potential_requirement_ids", [])}
    closing = {"id": "letter_3", "kind": "letter", "role": "closing",
        "purpose": "State one practical contribution to a JD need in prospective language and close naturally; do not add a second case study or repeat metrics.",
        "evidence": selected, "target_terms": [], "target_words": 45, "max_words": 60,
        "primary_requirement_id": None, "potential_requirement_ids": []}
    return bullets + [summary, opening, proof_paragraph, closing]
