"""Resumable v3 application coordinator."""

from __future__ import annotations

import json
from pathlib import Path

from .assessment_v3 import required_checks_pass
from .canonical import load_canonical_v3
from .decisions import choice, load_policy
from .generation import run_writing_v3
from .layout_v3 import build_resume_data
from .models import Application
from .planning_v3 import build_blueprint, planning_cases
from .provider import OpenRouter, load_key
from .records import AssessmentV3, Blueprint, LayoutSelection
from .rendering import render_application
from .reporting import write_coverage_report
from .skills import analyze_job_v3, classify_skills
from .store import RunStore, digest


def _planning_decisions(store, provider, cases):
    saved = store.state.get("planning_v3_decisions")
    if saved is not None:
        return saved
    answers = {}
    for start in range(0, len(cases), 40):
        batch = cases[start:start + 40]
        for case in batch:
            size = len(json.dumps(case.state, ensure_ascii=False))
            if size > 75_000:
                raise ValueError(f"Planning case {case.id} exceeds 75000 serialized characters: {size}")
        questions = {case.id: choice(case.question, case.criteria) for case in batch}
        answers.update(provider.decide({"cases": {case.id: case.state for case in batch}}, questions))
    store.state["planning_v3_decisions"] = answers
    store.save()
    return answers


def _export_application(blueprint: Blueprint, result: dict, application_date: str) -> dict:
    texts = result["texts"]
    layout = LayoutSelection.model_validate(result["layout"])
    resume = build_resume_data(blueprint, texts, layout.selected_ids)
    letter_ids = [item.id for item in blueprint.envelopes if item.kind == "letter_paragraph"]
    application = {
        "company_name": blueprint.job.company,
        "resume": resume,
        "cover_letter": {"date": application_date, "company_address": "", "salutation": "Dear Hiring Team",
                         "paragraphs": [texts[item_id] for item_id in letter_ids]},
    }
    return Application.model_validate(application).model_dump()


def execute_v3(root: Path, folder: Path):
    store = RunStore(folder)
    config = json.loads((folder / "inputs" / "config.json").read_text(encoding="utf-8"))
    policy = load_policy(folder / "inputs" / "decisions.json")
    canonical = load_canonical_v3(folder / "inputs" / "canonical.yaml")
    jd = (folder / "jd.md").read_text(encoding="utf-8")
    provider = OpenRouter(store, config, load_key(root))
    store.state["status"] = "RUNNING"
    store.save()
    try:
        store.begin_stage("planning_v3")
        job = analyze_job_v3(store, provider, policy, jd)
        skills, groups, skill_issues = classify_skills(provider, policy, job)
        cases = planning_cases(canonical, job)
        decisions = _planning_decisions(store, provider, cases)
        blueprint = build_blueprint(canonical, job, skills, groups, decisions)
        store.state["blueprint_v3"] = blueprint.model_dump(mode="json")
        store.state["skill_v3_issues"] = [item.model_dump(mode="json") for item in skill_issues]
        store.write("blueprint.json", blueprint.model_dump(mode="json"))
        store.record_stage("planning_v3")

        result = run_writing_v3(store, provider, policy, blueprint, canonical.profile)
        if "texts" not in result:
            store.state["status"] = "REVIEW_REQUIRED"
            store.save()
            return store.state
        application = _export_application(blueprint, result, store.state["application_date"])
        store.write("application.json", application)
        store.write("profile.json", canonical.profile)
        application_hash = digest(application)
        render_folder = folder / "renders" / application_hash[:12]
        rendered = render_application(application, canonical.profile, render_folder)
        report = AssessmentV3.model_validate(result["assessment"])
        layout = LayoutSelection.model_validate(result["layout"])
        if skill_issues:
            report.issues.extend(skill_issues)
            report.unresolved.extend(item.code + ":" + ",".join(item.node_ids) for item in skill_issues)
            report.unresolved = sorted(set(report.unresolved))
            report.passed = False
        accepted = required_checks_pass(report) and layout.checks["resume_one_page"] and rendered["checks"]["passed"] and not skill_issues
        status = "ACCEPTED_EXPERIMENTAL" if accepted else "REVIEW_REQUIRED"
        usage = {"http_attempts": store.state.get("http_attempts", 0),
                 "logical_jev_questions": store.state.get("logical_jev_questions", 0),
                 "reported_cost_usd": store.state.get("cost_usd", 0.0),
                 "stages": store.state.get("stage_usage", [])}
        coverage = write_coverage_report(folder, blueprint, report, layout, usage)
        store.state.update({
            "status": status, "application_hash": application_hash,
            "artifacts": {"resume": rendered["resume"], "cover_letter": rendered["cover_letter"],
                          "coverage": str(folder / "coverage.md"), "page_counts": rendered["page_counts"],
                          "checks": rendered["checks"]},
            "coverage_summary": coverage,
        })
        store.write("latest-render.json", {**rendered, "status": status})
        store.write("decision_trace.json", {
            "policy": policy, "job": job.model_dump(mode="json"),
            "skills": [item.model_dump(mode="json") for item in skills],
            "skill_groups": [item.model_dump(mode="json") for item in groups],
            "planning": decisions, "assessment": result["assessment"],
            "layout": result["layout"], "events": store.state["events"],
        })
        store.save()
        if accepted:
            store.write("release.json", {"status": status, "application_hash": application_hash,
                                         "artifacts": store.state["artifacts"],
                                         "calibration": "Experimental categorical checks; no ATS or interview guarantee"})
        return store.state
    except Exception as exc:
        store.state["status"] = "STOPPED"
        store.event("RUN_STOPPED", error_type=type(exc).__name__)
        raise
