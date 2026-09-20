"""Actual ReportLab-based resume measurement and v3 experience fitting."""

from __future__ import annotations

from io import BytesIO
from itertools import combinations, product
import json

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import KeepTogether, SimpleDocTemplate

from renderer.build import (
    MINIMUM_BODY_FONT_PT, resume_document_options, resume_flowables,
)

from .records import Blueprint, LayoutSelection


AVAILABLE_HEIGHT_PT = letter[1] - 72.0
AVAILABLE_WIDTH_PT = letter[0] - 72.0


def _height(flowable, width: float) -> float:
    if isinstance(flowable, KeepTogether):
        content = getattr(flowable, "_content", [])
        return sum(_height(item, width) for item in content)
    _, height = flowable.wrap(width, AVAILABLE_HEIGHT_PT)
    return float(height + max(0, flowable.getSpaceBefore()) + max(0, flowable.getSpaceAfter()))


def measure_resume(application_resume: dict, profile: dict) -> dict:
    flowables = resume_flowables(application_resume, profile)
    predicted_height = sum(_height(item, AVAILABLE_WIDTH_PT) for item in flowables)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, **resume_document_options(profile))
    document.build(resume_flowables(application_resume, profile))
    buffer.seek(0)
    pages = len(PdfReader(buffer).pages)
    return {
        "page_count": pages,
        "predicted_height_pt": predicted_height,
        "available_height_pt": AVAILABLE_HEIGHT_PT,
        "overflow_pt": max(0.0, predicted_height - AVAILABLE_HEIGHT_PT),
        "resume_one_page": pages == 1,
        "minimum_body_font_pt": MINIMUM_BODY_FONT_PT,
    }


def _predicted_height(application_resume: dict, profile: dict) -> float:
    return sum(_height(item, AVAILABLE_WIDTH_PT)
               for item in resume_flowables(application_resume, profile))


def build_resume_data(blueprint: Blueprint, texts: dict[str, str], selected_ids: list[str]) -> dict:
    selected = set(selected_ids)
    candidate_by_id = {item.id: item for item in blueprint.candidates}
    employers = blueprint.fixed_fields["employers"]
    experience = []
    for employer in employers:
        candidate_ids = [item.id for item in blueprint.candidates
                         if item.employer_id == employer["id"] and item.id in selected]
        if not candidate_ids:
            raise ValueError(f"No selected candidate for employer {employer['id']}")
        experience.append({
            "title": employer["titles"][0], "company": employer["company"], "period": employer["period"],
            "bullets": [texts[f"experience.{item_id}"] for item_id in candidate_ids],
        })
    item_by_id = {item.id: item for item in blueprint.skills}
    skills = [{"label": group.label, "value": ", ".join(item_by_id[item_id].display_text for item_id in group.item_ids)}
              for group in blueprint.skill_groups]
    if not skills:
        skills = [{"label": "Role capabilities", "value": blueprint.job.thesis}]
    summary_ids = [item.id for item in blueprint.envelopes if item.kind == "summary_sentence"]
    project_ids = [item.id for item in blueprint.envelopes if item.kind == "project_bullet"]
    return {
        "summary": " ".join(texts[item_id].strip() for item_id in summary_ids),
        "skills": skills,
        "experience": experience,
        "projects": [{"name": blueprint.prototype.name, "period": blueprint.prototype.period,
                      "bullets": [texts[item_id] for item_id in project_ids]}],
        "education": blueprint.fixed_fields["education"],
    }


def _score(blueprint: Blueprint, ids: tuple[str, ...]) -> tuple:
    selected = [item for item in blueprint.candidates if item.id in ids]
    component_by_id = {item.id: item for item in blueprint.job.components}
    direct_core = set()
    partial_core = set()
    supporting = set()
    for candidate in selected:
        for component_id, status in candidate.component_support.items():
            priority = component_by_id[component_id].priority
            if priority == "CORE" and status == "DIRECT":
                direct_core.add(component_id)
            elif priority == "CORE" and status in ("PARTIAL", "ADJACENT"):
                partial_core.add(component_id)
            elif priority == "SUPPORTING" and status in ("DIRECT", "PARTIAL"):
                supporting.add(component_id)
    specificity = sum({"CONCRETE_OUTCOME": 2, "CONCRETE_WORK": 1}.get(item.specificity, 0) for item in selected)
    return len(direct_core), len(partial_core), len(supporting), len(selected), specificity


def select_fitting_experience(blueprint: Blueprint, texts: dict[str, str], leaf_report,
                              profile: dict) -> LayoutSelection:
    by_employer = []
    for employer in blueprint.fixed_fields["employers"]:
        ids = [item.id for item in blueprint.candidates if item.employer_id == employer["id"]]
        if not ids:
            raise ValueError(f"No candidate available for employer {employer['id']}")
        options = [combo for size in range(1, min(4, len(ids)) + 1) for combo in combinations(ids, size)]
        by_employer.append(options)
    ranked = []
    for employer_choice in product(*by_employer):
        ids = tuple(item_id for group in employer_choice for item_id in group)
        resume = build_resume_data(blueprint, texts, list(ids))
        ranked.append((ids, _score(blueprint, ids), _predicted_height(resume, profile), resume))
    # Actual PDF pagination is authoritative. Predicted height only orders equal
    # semantic subsets and avoids rendering thousands of obviously weaker ones.
    ranked.sort(key=lambda item: (item[1], tuple(sorted(item[0]))), reverse=True)
    render_cache = {}
    chosen = None
    smallest = None
    for ids, score, predicted, resume in ranked:
        signature = json.dumps(resume, sort_keys=True, ensure_ascii=False)
        measurement = render_cache.get(signature)
        if measurement is None:
            measurement = measure_resume(resume, profile)
            render_cache[signature] = measurement
        if smallest is None or (measurement["page_count"], measurement["predicted_height_pt"], ids) < (
                smallest[1]["page_count"], smallest[1]["predicted_height_pt"], smallest[0]):
            smallest = (ids, measurement)
        if measurement["resume_one_page"]:
            chosen = (ids, measurement)
            break
    if chosen:
        ids, measurement = chosen
        issues = []
    else:
        ids, measurement = smallest
        issues = ["PAGE_OVERFLOW"]
    selected = set(ids)
    omitted = dict(blueprint.unselected_reasons)
    for candidate in blueprint.candidates:
        if candidate.id not in selected:
            omitted[candidate.id] = "page space after preserving stronger component coverage"
    return LayoutSelection(
        selected_ids=list(ids), omitted=omitted,
        predicted_height_pt=measurement["predicted_height_pt"],
        available_height_pt=measurement["available_height_pt"],
        overflow_pt=measurement["overflow_pt"],
        checks={"resume_one_page": measurement["resume_one_page"], "page_count": measurement["page_count"],
                "minimum_body_font_pt": MINIMUM_BODY_FONT_PT, "issues": issues,
                "measured_with_shared_flowables": True},
    )
