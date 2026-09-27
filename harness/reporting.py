"""Human-readable and machine-readable v3 coverage reports."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .records import AssessmentV3, Blueprint, LayoutSelection


def coverage_data(blueprint: Blueprint, report: AssessmentV3, layout: LayoutSelection, usage: dict) -> dict:
    candidate_by_id = {item.id: item for item in blueprint.candidates}
    counts = Counter(candidate_by_id[item_id].employer_id for item_id in layout.selected_ids)
    skills = []
    group_by_item = {item_id: group.label for group in blueprint.skill_groups for item_id in group.item_ids}
    for item in blueprint.skills:
        skills.append({"term": item.exact_term, "kind": item.kind.value, "group": group_by_item.get(item.id, "role/experience context"),
                       "display_text": item.display_text, "centrality": item.centrality})
    employers = []
    for employer in blueprint.fixed_fields["employers"]:
        omitted = [{"candidate_id": candidate_id, "reason": reason}
                   for candidate_id, reason in layout.omitted.items()
                   if candidate_id in candidate_by_id and candidate_by_id[candidate_id].employer_id == employer["id"]]
        employers.append({"id": employer["id"], "company": employer["company"],
                          "selected_bullets": counts[employer["id"]], "omitted": omitted})
    return {
        "status": "PASS" if report.passed and layout.checks.get("resume_one_page") else "REVIEW_REQUIRED",
        "components": [{"id": item.id, "text": item.text, **report.component_coverage[item.id]}
                       for item in blueprint.job.components],
        "skills": skills,
        "employers": employers,
        "project": {"name": blueprint.prototype.name, "period": blueprint.prototype.period,
                    "purpose": blueprint.job.thesis, "local_scope": True,
                    "source_system_pattern": blueprint.prototype.source_system_id,
                    "restrictions": blueprint.prototype.restrictions},
        "issues": [item.model_dump(mode="json") for item in report.issues],
        "layout": layout.model_dump(mode="json"),
        "usage": usage,
    }


def write_coverage_report(folder: Path, blueprint: Blueprint, report: AssessmentV3,
                          layout: LayoutSelection, usage: dict) -> dict:
    data = coverage_data(blueprint, report, layout, usage)
    (folder / "coverage.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [f"# Coverage - {blueprint.job.company} / {blueprint.job.role}", "",
             f"Status: **{data['status']}**", ""]
    if blueprint.job.brief is not None:
        lines += ["## Role brief", "", blueprint.job.brief.summary, ""]
        lines += [f"- Must-have: {item}" for item in blueprint.job.brief.must_haves] + [""]
    lines += ["## Unresolved in JD reading", ""]
    lines += [f"- `{item.kind}` {item.node_id} {item.text}".replace("  ", " ") for item in blueprint.job.unresolved] or ["- None."]
    lines += ["", "## JD work components", "",
             "| Component | Priority | Status | Visible evidence |", "|---|---|---|---|"]
    for component in data["components"]:
        lines.append(f"| {component['text']} | {component['priority']} | {component['status']} | {', '.join(component['expressed_ids']) or 'none'} |")
    lines += ["", "## Skills hierarchy", "", "| Exact JD term | Kind | Display group | Centrality |",
              "|---|---|---|---|"]
    for item in data["skills"]:
        lines.append(f"| {item['term']} | {item['kind']} | {item['group']} | {item['centrality']} |")
    lines += ["", "## Employer allocation", "", "| Employer | Selected bullets | Omitted useful candidates |",
              "|---|---:|---|"]
    for employer in data["employers"]:
        omitted = "; ".join(f"{item['candidate_id']}: {item['reason']}" for item in employer["omitted"]) or "none"
        lines.append(f"| {employer['company']} | {employer['selected_bullets']} | {omitted} |")
    lines += ["", "## Independent project", "",
              f"- **{data['project']['name']}** (period intentionally blank)",
              f"- JD purpose: {data['project']['purpose']}",
              "- Scope: independent local workflow; no employer metric, company scale, invented date, or repository URL.",
              "", "## Outstanding issues", ""]
    if data["issues"]:
        lines.extend(f"- `{item['code']}` - {item['instruction']}" for item in data["issues"])
    else:
        lines.append("- None.")
    lines += ["", "## Local PDF checks", "",
              f"- Resume pages: {layout.checks.get('page_count')}",
              f"- Minimum body font: {layout.checks.get('minimum_body_font_pt')} pt",
              f"- Shared renderer measurement: {layout.checks.get('measured_with_shared_flowables')}",
              "- These are local layout checks, not an ATS-pass or interview prediction.",
              "", "## Usage", "",
              f"- Writer/Jev HTTP attempts: {usage.get('http_attempts', 0)}",
              f"- Logical Jev questions: {usage.get('logical_jev_questions', 0)}",
              f"- Reported total cost: USD {usage.get('reported_cost_usd', 0):.6f}"]
    (folder / "coverage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return data
