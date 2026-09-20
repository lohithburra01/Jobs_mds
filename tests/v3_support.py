from copy import deepcopy


ARCHIVE_HASH = "a" * 64


def source(line: int, quote: str) -> dict:
    return {
        "archive_sha256": ARCHIVE_HASH,
        "start_line": line,
        "end_line": line,
        "quote": quote,
    }


def make_canonical_v3_fixture() -> dict:
    return {
        "schema_version": 3,
        "source_archive": "archive/canonical-v2.md",
        "source_archive_sha256": ARCHIVE_HASH,
        "profile": {"name": "Test Candidate", "phone": "123", "location": "Test City"},
        "education": [
            {"degree": "MS Data", "school": "School A", "year": "2025"},
            {"degree": "BS Engineering", "school": "School B", "year": "2022"},
        ],
        "identity": {"professional_spine": "Builds controlled automation systems."},
        "administrative": {},
        "policies": {
            "stack_retrofit": "functional",
            "max_bullets_per_employer": 4,
            "include_independent_project": True,
        },
        "employers": [
            {
                "id": "one",
                "company": "One",
                "titles": ["Engineer"],
                "period": "2025",
                "status_text": "Built and used internally.",
                "boundary_ids": ["one-boundary"],
                "systems": [
                    {
                        "id": "one.system",
                        "narrative": "Built system one.",
                        "source_refs": [source(1, "Built system one.")],
                        "problem_fact_ids": [],
                        "input_fact_ids": [],
                        "action_fact_ids": ["one.action"],
                        "output_fact_ids": ["one.output"],
                        "outcome_fact_ids": [],
                        "metric_ids": ["one.metric"],
                        "boundary_ids": ["one-boundary"],
                        "status_fact_ids": [],
                        "accomplishments": [
                            {
                                "id": "one.accomplishment",
                                "system_id": "one.system",
                                "purpose": "Show system delivery.",
                                "fact_ids": ["one.action", "one.output"],
                                "metric_ids": ["one.metric"],
                                "boundary_ids": ["one-boundary"],
                            }
                        ],
                    }
                ],
            },
            {
                "id": "two",
                "company": "Two",
                "titles": ["Analyst"],
                "period": "2022",
                "status_text": "Production system.",
                "boundary_ids": [],
                "systems": [
                    {
                        "id": "two.system",
                        "narrative": "Built system two.",
                        "source_refs": [source(2, "Built system two.")],
                        "problem_fact_ids": [],
                        "input_fact_ids": [],
                        "action_fact_ids": ["two.action"],
                        "output_fact_ids": [],
                        "outcome_fact_ids": [],
                        "metric_ids": [],
                        "boundary_ids": [],
                        "status_fact_ids": [],
                        "accomplishments": [
                            {
                                "id": "two.accomplishment",
                                "system_id": "two.system",
                                "purpose": "Show data work.",
                                "fact_ids": ["two.action"],
                                "metric_ids": [],
                                "boundary_ids": [],
                            }
                        ],
                    }
                ],
            },
        ],
        "facts": [
            {"id": "one.action", "employer_id": "one", "system_id": "one.system", "kind": "action", "text": "Built it.", "source_refs": [source(1, "Built system one.")]},
            {"id": "one.output", "employer_id": "one", "system_id": "one.system", "kind": "output", "text": "Produced output.", "source_refs": [source(1, "Built system one.")]},
            {"id": "two.action", "employer_id": "two", "system_id": "two.system", "kind": "action", "text": "Built another system.", "source_refs": [source(2, "Built system two.")]},
        ],
        "metrics": [
            {"id": "one.metric", "employer_id": "one", "system_id": "one.system", "display_text": "10 per day", "meaning": "Daily volume", "status": "achieved", "source_refs": [source(1, "Built system one.")]},
            {"id": "one.target", "employer_id": "one", "system_id": "one.system", "display_text": "100 target", "meaning": "Future target", "status": "target", "source_refs": [source(1, "Built system one.")]},
        ],
        "boundaries": [
            {"id": "one-boundary", "scope_ids": ["one", "one.system"], "text": "Do not inflate status.", "source_refs": [source(1, "Built system one.")]}
        ],
        "prototype_pattern": {
            "statement": "Builds a local prototype before larger implementation.",
            "local_scope": "Independent local workflow only.",
            "publication_status": "Published on GitHub; exact repository unspecified.",
            "source_session_note": "User correction, 20 September 2026.",
            "restrictions": ["No employer metrics or company scale."],
            "metric_ids": [],
        },
        "migration": [
            {"start_line": 1, "end_line": 1, "destination_ids": ["one.system"], "disposition": "structured"},
            {"start_line": 2, "end_line": 2, "destination_ids": ["two.system"], "disposition": "structured"},
        ],
    }


def validate_canonical_fixture(data: dict):
    from harness.canonical import validate_canonical_v3

    return validate_canonical_v3(deepcopy(data))

