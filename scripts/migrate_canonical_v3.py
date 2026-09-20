"""One-time, deterministic migration of the v2 Markdown canonical to v3 YAML."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from harness.canonical import check_migration, validate_canonical_v3


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive" / "canonical-v2.md"
OUTPUT = ROOT / "canonical.yaml"
REPORT = ROOT / "migration-report.json"


SYSTEM_SPECS = [
    ("corominas", "corominas.multi_tenant", "## Capability block 1: Multi-tenant LLM pipeline architecture", [
        ("problem", "A 200-client operation needed repeatable delivery without client-specific code branches."),
        ("action", "Built a configuration-driven, multi-tenant LLM pipeline from intake through validation, approval, publication, confirmation, and state tracking."),
        ("output", "Converted client onboarding and variation into configuration instead of duplicated workflow logic."),
        ("outcome", "Rolled the client-deliverable and approval cycle across the full 200-client portfolio while retaining exception handling and final approval."),
    ]),
    ("corominas", "corominas.llm_harness", "## Capability block 2: LLM harness and cost control", [
        ("action", "Built provider-independent LLM orchestration with sub-agent techniques, prompt caching, context management, loop reduction, and memory optimization."),
        ("output", "Separated model-provider calls from orchestration so a model change became configuration rather than a workflow rewrite."),
        ("outcome", "Reduced inference cost by more than 90 percent, from dollar-scale to cent-scale per operation, without quality regression."),
    ]),
    ("corominas", "corominas.quality_gate", "## Capability block 3: Deterministic quality gate", [
        ("action", "Built a deterministic validation layer between generation and human review for format, completeness, factual consistency, and structure."),
        ("output", "Withheld failed output and made prompt or model changes comparable against stable checks."),
        ("outcome", "Automated routine validation while preserving final human judgment."),
    ]),
    ("corominas", "corominas.approval", "## Capability block 4: Human-in-the-loop approval system", [
        ("action", "Built a client-facing preview, inline-editing, approval, publication, and confirmation flow."),
        ("output", "Made approval a defined client-controlled state transition rather than an informal team handoff."),
        ("outcome", "Reduced approval-to-publish time from days to under 60 seconds."),
    ]),
    ("corominas", "corominas.agent_ops", "## Capability block 5: Multi-agent operational orchestration", [
        ("action", "Built domain-specific agents across Slack with an Airtable ledger for queryable actions and human escalation for cross-system risk."),
        ("output", "Separated routine autonomous requests from risky changes that required a human ticket."),
        ("outcome", "Removed a routine engineering bottleneck and replaced ad hoc status chasing with visible notifications and durable history."),
    ]),
    ("corominas", "corominas.generated_workflows", "## Capability block 6: Workflow infrastructure as generated code", [
        ("action", "Built Python generators that emit and maintain workflow definitions as deterministic infrastructure."),
        ("output", "Made workflow patterns reviewable, reproducible, and consistently regenerable."),
        ("outcome", "Replaced repeated manual workflow editing with reusable generation logic."),
    ]),
    ("corominas", "corominas.security_response", "## Capability block 7: Security response and hardening", [
        ("action", "Led a technical response to a third-party compromise by identifying the vector, auditing automation, sweeping the portfolio, and hardening the API surface."),
        ("output", "Converted the portfolio sweep into a passive ongoing scanner and authored a standing security policy."),
        ("outcome", "Turned a one-off incident investigation into an ongoing posture-monitoring control."),
    ]),
    ("formula_dream", "formula.event_pipeline", "## System 1: Event-driven production and publishing pipeline", [
        ("problem", "Completed media needed reliable multi-platform publication without manual handling."),
        ("action", "Built an event-driven and scheduled pipeline across Python jobs, Google Drive, n8n, external APIs, grounded LLM generation, and publishing endpoints."),
        ("output", "Added durable posted-state markers, scheduled recovery, retry backoff, strict JSON contracts, and diagnostic failure links."),
        ("outcome", "Automated asset-to-publication handling while preventing duplicate publication and making failures diagnosable."),
    ]),
    ("formula_dream", "formula.workflow_generator", "## System 2: n8n workflow-generation system", [
        ("action", "Built a Claude-assisted generator for complete importable n8n workflow JSON aligned with established credential conventions."),
        ("output", "Reused the generation approach across two production systems and more than 23 workflows."),
        ("outcome", "Reduced idea-to-running-workflow time to under 10 minutes."),
    ]),
    ("formula_dream", "formula.event_templates", "## System 3: Reusable event-template automation", [
        ("action", "Built parameterized templates that wait for live event state and combine results, statistics, commentary, context, AI-generated copy, and publishing."),
        ("output", "Passed changing event context as data through one maintained template."),
        ("outcome", "Replaced event-by-event recreation with a reusable data-driven workflow."),
    ]),
    ("formula_dream", "formula.information_aggregation", "## System 4: Recurring information aggregation", [
        ("action", "Built a recurring pipeline that collected and processed information from heterogeneous community and web sources."),
        ("output", "Created a consolidated information layer refreshed at an approximately daily cadence."),
        ("outcome", "Replaced dependence on a single feed with recurring multi-source ingestion."),
    ]),
    ("formula_dream", "formula.formulytics", "## Personally attributable Formula Dream impact", [
        ("action", "Built and operated the Formulytics presence and its automated operating system."),
        ("outcome", "Supported audience scale of 200M+ cumulative Instagram views, roughly 20M monthly Facebook views at peak, and 30K Instagram followers."),
    ]),
    ("think_round", "think.context_memory", "## Context-aware conversation architecture", [
        ("action", "Built a context-aware LLM conversation system with persistent memory, confidence handling, ACE context, and personalized behavior."),
        ("output", "Combined Python, FastAPI, asynchronous services, APIs, orchestration, and multi-provider evaluation in a retained-context conversation path."),
        ("outcome", "Produced a core architecture suitable for continued developer work and pilot preparation."),
        ("status", "The product remained under mental-health board review and was not clinically validated or approved."),
    ]),
    ("think_round", "think.safety_evaluation", "## Safety and evaluation architecture", [
        ("action", "Built a bounded fail-closed response path that generates, parses, evaluates, and releases only output that passes safety checks."),
        ("output", "Implemented harmful-content filtering, crisis detection and routing, professional boundaries, minor-user protections, and layered controls."),
        ("outcome", "Preserved conversational responsiveness while checking model output before it reached a vulnerable user."),
        ("status", "The safety design was ready for review and pilot preparation; it did not establish clinical efficacy."),
    ]),
    ("think_round", "think.multi_agent_platform", "## ThinkLife multi-agent platform architecture", [
        ("action", "Contributed to platform architecture for parallel development of healing, onboarding, FAQ, and storytelling agents."),
        ("output", "Separated specialized agent responsibilities within a shared platform direction."),
        ("status", "Zoe reached board review; the other specialized agents were still under construction."),
    ]),
    ("cognizant", "cognizant.ingestion", "## Automated data ingestion and processing", [
        ("action", "Built automated Python, SQL, Apache Spark, and PySpark-style data-ingestion pipelines."),
        ("output", "Fed downstream KPI and analytics workflows with production-scale transformed data."),
        ("outcome", "Maintained ingestion at more than 50 million rows per day."),
    ]),
    ("cognizant", "cognizant.kpi_latency", "## Data-to-KPI acceleration", [
        ("action", "Optimized the path from source data through downstream KPI delivery."),
        ("outcome", "Reduced data-to-KPI latency from roughly 48 hours to roughly 2 hours."),
    ]),
    ("cognizant", "cognizant.aws_etl", "## AWS ETL optimization", [
        ("action", "Optimized ETL workflows using AWS S3, Lambda, and Glue."),
        ("outcome", "Reduced infrastructure cost measurably without a confirmed exact percentage or amount."),
    ]),
    ("cognizant", "cognizant.data_quality", "## Data quality and maintainability foundation", [
        ("action", "Used data validation and pipeline testing with explicit transformations and downstream KPI dependencies."),
        ("output", "Built production experience in throughput, cloud ETL, distributed processing, and maintainable data contracts."),
    ]),
]


METRIC_SPECS = [
    ("corominas.clients", "corominas.multi_tenant", "200-client portfolio", "Operating portfolio scale", "achieved", "## Authorized Corominas metrics"),
    ("corominas.monthly_volume", "corominas.multi_tenant", "1,200+ pieces per month", "Full-portfolio production volume", "achieved", "## Authorized Corominas metrics"),
    ("corominas.growth_target", "corominas.multi_tenant", "about 200 to 3,000 clients by 2030", "Architecture-supported future growth target", "target", "## Authorized Corominas metrics"),
    ("corominas.inference_cost", "corominas.llm_harness", "over 90% reduction", "Inference-cost reduction without quality regression", "achieved", "## Authorized Corominas metrics"),
    ("corominas.approval_latency", "corominas.approval", "days to under 60 seconds", "Approval-to-publish latency", "achieved", "## Authorized Corominas metrics"),
    ("formula.workflows", "formula.workflow_generator", "23+ workflows", "Generated workflows", "achieved", "## System 2: n8n workflow-generation system"),
    ("formula.workflow_time", "formula.workflow_generator", "under 10 minutes", "Idea-to-running-workflow time", "achieved", "## System 2: n8n workflow-generation system"),
    ("formula.instagram_views", "formula.formulytics", "200M+ cumulative Instagram views", "Personally attributable Formulytics audience scale", "achieved", "## Personally attributable Formula Dream impact"),
    ("formula.facebook_views", "formula.formulytics", "roughly 20M Facebook views per month at peak", "Personally attributable Formulytics peak audience scale", "achieved", "## Personally attributable Formula Dream impact"),
    ("formula.instagram_followers", "formula.formulytics", "30K Instagram followers", "Personally attributable Formulytics following", "achieved", "## Personally attributable Formula Dream impact"),
    ("cognizant.daily_rows", "cognizant.ingestion", "50M+ rows per day", "Production ingestion scale", "achieved", "## Automated data ingestion and processing"),
    ("cognizant.kpi_latency", "cognizant.kpi_latency", "roughly 48 hours to roughly 2 hours", "Data-to-KPI latency reduction", "achieved", "## Data-to-KPI acceleration"),
]


EMPLOYERS = {
    "corominas": ("Corominas Consulting", ["Manager, AI & Automation"], "Jun 2026 - Sep 2026", "Full-portfolio client-deliverable and approval cycle; broader workstreams had mixed completion states.", "## Corominas selection rule"),
    "formula_dream": ("Formula Dream", ["AI Automation Engineer", "AI Automation Developer"], "Mar 2026 - Jun 2026", "Remote contract; primary stage 0-to-1.", "## Formula Dream boundaries"),
    "think_round": ("Think Round Inc.", ["AI Engineer", "AI Automation Engineer"], "Apr 2025 - Mar 2026", "Zoe was under mental-health board review, not approved or clinically validated.", "## Think Round boundaries"),
    "cognizant": ("Cognizant Technology Solutions", ["Program Analyst"], "Feb 2022 - Aug 2023", "Production enterprise data operations.", "## Cognizant boundaries"),
}


def main() -> None:
    raw = ARCHIVE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8-sig").splitlines()
    headings = [(i + 1, line) for i, line in enumerate(lines) if line.startswith("#")]
    starts = {heading: line_no for line_no, heading in headings}

    def section(heading: str) -> tuple[int, int, str]:
        start = starts[heading]
        following = [line_no for line_no, _ in headings if line_no > start]
        end = min(following) - 1 if following else len(lines)
        return start, end, "\n".join(lines[start - 1:end]).strip()

    def top_section(heading: str) -> tuple[int, int, str]:
        start = starts[heading]
        following = [line_no for line_no, text in headings if line_no > start and text.startswith("# ")]
        end = min(following) - 1 if following else len(lines)
        return start, end, "\n".join(lines[start - 1:end]).strip()

    def ref(heading: str) -> dict:
        start, end, quote = section(heading)
        return {"archive_sha256": digest, "start_line": start, "end_line": end, "quote": quote}

    boundary_headings = {
        "corominas": "## Corominas selection rule",
        "formula_dream": "## Formula Dream boundaries",
        "think_round": "## Think Round boundaries",
        "cognizant": "## Cognizant boundaries",
    }
    boundaries = []
    for employer_id, heading in boundary_headings.items():
        boundaries.append({
            "id": f"{employer_id}.boundary",
            "scope_ids": [employer_id],
            "text": section(heading)[2],
            "source_refs": [ref(heading)],
        })

    facts = []
    systems_by_employer = {key: [] for key in EMPLOYERS}
    system_to_employer = {}
    for employer_id, system_id, heading, fact_specs in SYSTEM_SPECS:
        system_to_employer[system_id] = employer_id
        fact_ids = {kind: [] for kind in ("problem", "input", "action", "output", "outcome", "status")}
        for index, (kind, text) in enumerate(fact_specs, 1):
            fact_id = f"{system_id}.{kind}.{index}"
            fact_ids[kind].append(fact_id)
            facts.append({
                "id": fact_id,
                "employer_id": employer_id,
                "system_id": system_id,
                "kind": kind,
                "text": text,
                "source_refs": [ref(heading)],
            })
        systems_by_employer[employer_id].append({
            "id": system_id,
            "narrative": section(heading)[2],
            "source_refs": [ref(heading)],
            "problem_fact_ids": fact_ids["problem"],
            "input_fact_ids": fact_ids["input"],
            "action_fact_ids": fact_ids["action"],
            "output_fact_ids": fact_ids["output"],
            "outcome_fact_ids": fact_ids["outcome"],
            "metric_ids": [],
            "boundary_ids": [f"{employer_id}.boundary"],
            "status_fact_ids": fact_ids["status"],
            "accomplishments": [{
                "id": f"{system_id}.accomplishment",
                "system_id": system_id,
                "purpose": f"Demonstrate the distinct work and result in {heading.split(':', 1)[-1].strip()}.",
                "fact_ids": [item for values in fact_ids.values() for item in values],
                "metric_ids": [],
                "boundary_ids": [f"{employer_id}.boundary"],
            }],
        })

    metrics = []
    for metric_id, system_id, display, meaning, status, heading in METRIC_SPECS:
        employer_id = system_to_employer[system_id]
        metrics.append({
            "id": metric_id,
            "employer_id": employer_id,
            "system_id": system_id,
            "display_text": display,
            "meaning": meaning,
            "status": status,
            "source_refs": [ref(heading)],
        })
        system = next(item for item in systems_by_employer[employer_id] if item["id"] == system_id)
        system["metric_ids"].append(metric_id)
        system["accomplishments"][0]["metric_ids"].append(metric_id)

    employers = []
    for employer_id, (company, titles, period, status, _) in EMPLOYERS.items():
        employers.append({
            "id": employer_id,
            "company": company,
            "titles": titles,
            "period": period,
            "status_text": status,
            "boundary_ids": [f"{employer_id}.boundary"],
            "systems": systems_by_employer[employer_id],
        })

    destination_by_heading = {
        "# Personal and administrative facts": ["profile", "administrative"],
        "# Education": ["education"],
        "## Stevens Institute of Technology": ["education.stevens"],
        "## JNTU K": ["education.jntu"],
        "# Authoritative career chronology": list(EMPLOYERS),
        "# Professional identity": ["identity.professional_spine"],
        "# Scaling-stage model": ["identity.scaling_stages"],
        "## 0-to-1": ["formula_dream"],
        "## 1-to-10": ["corominas", "think_round", "cognizant"],
        "# Agentic maintainability and pipeline discipline": ["identity.maintainability"],
        "## Core projection": ["identity.maintainability"],
        "## Working method": ["identity.working_method"],
        "## Resume-level language": ["identity.claim_boundaries"],
        "# Confirmed technology inventory": ["policies.stack_retrofit"],
        "## Universal pipeline and stack-agnostic authority": ["policies.stack_retrofit"],
        "## Separate capability-proof rule": ["policies.capability_proof"],
        "## AI, LLM, and agentic systems": ["administrative.known_technology_examples"],
        "## Automation, reliability, and integration": ["administrative.known_technology_examples"],
        "## Cloud, data-platform, database, and observability breadth": ["administrative.known_technology_examples"],
        "## Software, platform, and data engineering": ["administrative.known_technology_examples"],
        "## Engineering work environment": ["administrative.known_technology_examples"],
        "# Global claim boundaries": ["identity.claim_boundaries"],
    }
    for employer_id, _, heading, _ in SYSTEM_SPECS:
        system_id = next(spec[1] for spec in SYSTEM_SPECS if spec[0] == employer_id and spec[2] == heading)
        destination_by_heading[heading] = [system_id]
    for employer_id, (_, _, _, _, boundary_heading) in EMPLOYERS.items():
        destination_by_heading[boundary_heading] = [f"{employer_id}.boundary"]
    destination_by_heading.update({
        "# Corominas Consulting": ["corominas"],
        "## Role identity and scaling stage": list(EMPLOYERS),
        "## Authorized Corominas metrics": [item[0] for item in METRIC_SPECS if item[0].startswith("corominas.")],
        "# Formula Dream": ["formula_dream"],
        "# Think Round Inc.": ["think_round"],
        "## Product context and status": ["think.context_memory", "think.safety_evaluation"],
        "## Think Round stack": ["administrative.known_technology_examples"],
        "# Cognizant Technology Solutions": ["cognizant"],
        "## Cognizant stack": ["administrative.known_technology_examples"],
    })

    migration = []
    for index, (start, heading) in enumerate(headings):
        end = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
        destination_ids = destination_by_heading.get(heading, [])
        disposition = "structured"
        if heading in {"# 01-CANONICAL.md", "## Purpose and authority", "## Fast routing index", "# Final canonical use rule"}:
            disposition = "superseded"
        elif heading in {"## Deliberate scope of this canonical", "# Projects"}:
            disposition = "archived"
        migration.append({
            "start_line": start,
            "end_line": end,
            "destination_ids": destination_ids,
            "disposition": disposition,
        })

    data = {
        "schema_version": 3,
        "source_archive": "archive/canonical-v2.md",
        "source_archive_sha256": digest,
        "profile": {"name": "Lohith Burra", "phone": "+4915124223947", "location": "Mannheim, Germany"},
        "education": [
            {"degree": "Master of Science - Data Science", "school": "Stevens Institute of Technology", "year": "2025"},
            {"degree": "Bachelor of Technology - Mechanical Engineering", "school": "JNTU K", "year": "2022"},
        ],
        "identity": {
            "professional_spine": "AI automation and agentic-systems engineer with a production data-engineering foundation.",
            "career_progression": "production data pipelines -> applied LLM and safety systems -> zero-to-one AI automation -> one-to-ten multi-tenant agentic operations",
            "maintainability": top_section("# Agentic maintainability and pipeline discipline")[2],
            "claim_boundaries": top_section("# Global claim boundaries")[2],
        },
        "administrative": {
            "citizenship": "Indian",
            "immigration_status": "German Opportunity Card / Chancenkarte, valid through April 2027",
            "relocation": "Open to relocation",
            "work_authorization_rules": top_section("# Personal and administrative facts")[2],
            "known_technology_examples": top_section("# Confirmed technology inventory")[2],
        },
        "policies": {"stack_retrofit": "functional", "max_bullets_per_employer": 4, "include_independent_project": True},
        "employers": employers,
        "facts": facts,
        "metrics": metrics,
        "boundaries": boundaries,
        "prototype_pattern": {
            "statement": "Before larger company implementations, Lohith builds a small-scale local version of the target workflow and adds it to GitHub.",
            "local_scope": "Independent local proof of the JD-relevant workflow; retrofit the JD stack functionally.",
            "publication_status": "Added to GitHub; exact repository URL and project date are not asserted unless supplied.",
            "source_session_note": "Binding user correction recorded 20 September 2026; this supersedes the archived no-project rule.",
            "restrictions": [
                "Do not reuse an employer metric, company scale, employer, title, or date.",
                "Do not invent a repository URL or project period.",
                "Describe a small local implementation and concrete output relevant to the JD.",
            ],
            "metric_ids": [],
        },
        "migration": migration,
    }
    canonical = validate_canonical_v3(data)
    OUTPUT.write_text(yaml.safe_dump(canonical.model_dump(mode="json"), sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    result = check_migration(canonical, ARCHIVE)
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["complete"]:
        raise SystemExit(json.dumps(result, indent=2))
    print(json.dumps({"complete": True, "archive_sha256": digest, "employers": len(employers), "systems": sum(map(len, systems_by_employer.values())), "facts": len(facts), "metrics": len(metrics)}, indent=2))


if __name__ == "__main__":
    main()
