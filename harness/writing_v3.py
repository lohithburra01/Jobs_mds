"""Build and validate the single coherent v3 writer request."""

from __future__ import annotations

from .records import Blueprint, Issue


def writer_payload(blueprint: Blueprint, texts: dict[str, str], writable_ids: list[str],
                   issues: list[Issue]) -> dict:
    envelope_by_id = {item.id: item for item in blueprint.envelopes}
    unknown = sorted(set(writable_ids) - set(envelope_by_id))
    if unknown:
        raise ValueError(f"Unknown writable envelope IDs: {unknown}")
    return {
        "task": "Write prose for exactly the supplied envelope IDs. Make no evidence, selection, scoring, or validation decisions.",
        "job": blueprint.job.model_dump(mode="json"),
        "outline": [item.model_dump(mode="json") for item in blueprint.envelopes],
        "writable_ids": list(writable_ids),
        "writable_envelopes": [envelope_by_id[item_id].model_dump(mode="json") for item_id in writable_ids],
        "complete_draft_read_only": dict(texts),
        "skills_read_only": {
            group.label: [next(item.display_text for item in blueprint.skills if item.id == item_id)
                          for item_id in group.item_ids]
            for group in blueprint.skill_groups
        },
        "candidates": [item.model_dump(mode="json") for item in blueprint.candidates],
        "prototype": blueprint.prototype.model_dump(mode="json"),
        "fixed_fields": blueprint.fixed_fields,
        "issues": [item.model_dump(mode="json") for item in issues],
        "constraints": [
            "Return JSON with one texts object and exactly the writable IDs.",
            "Do not add, remove, select, rank, score, or validate facts, skills, candidates, employers, or sections.",
            "Use the target terms only at logical workflow stages; stack retrofit is already authorized.",
            "Use plain recruiter-readable language and preserve all supplied metric statuses and boundaries.",
            "Word ranges are guidance only, not content to mention or a reason to omit substance.",
        ],
    }


def validate_writer_response(response: dict, writable_ids: list[str]) -> dict[str, str]:
    if not isinstance(response, dict) or set(response) != {"texts"} or not isinstance(response.get("texts"), dict):
        raise ValueError("Writer must return one texts object")
    texts = response["texts"]
    if set(texts) != set(writable_ids):
        raise ValueError("Writer must return exactly the supplied writable IDs")
    for item_id, value in texts.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Writer text for {item_id} must be a nonempty string")
    return {item_id: texts[item_id].strip() for item_id in writable_ids}
