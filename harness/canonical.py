import hashlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .records import CanonicalV3, SourceRef


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader: UniqueKeyLoader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate key in YAML: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)


def load_yaml_unique(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return yaml.load(handle, Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid canonical YAML: {exc}") from exc


def _duplicate(values: list[str], label: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {label}: {value}")
        seen.add(value)


def validate_canonical_v3(data: dict) -> CanonicalV3:
    try:
        canonical = CanonicalV3.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"invalid canonical v3: {exc}") from exc

    employer_ids = [item.id for item in canonical.employers]
    system_pairs = {
        system.id: employer.id
        for employer in canonical.employers
        for system in employer.systems
    }
    fact_by_id = {item.id: item for item in canonical.facts}
    metric_by_id = {item.id: item for item in canonical.metrics}
    boundary_by_id = {item.id: item for item in canonical.boundaries}
    accomplishment_ids = [
        item.id
        for employer in canonical.employers
        for system in employer.systems
        for item in system.accomplishments
    ]
    _duplicate(employer_ids, "employer id")
    _duplicate(list(system_pairs), "system id")
    _duplicate(list(fact_by_id), "fact id")
    _duplicate(list(metric_by_id), "metric id")
    _duplicate(list(boundary_by_id), "boundary id")
    _duplicate(accomplishment_ids, "accomplishment id")

    for fact in canonical.facts:
        if system_pairs.get(fact.system_id) != fact.employer_id:
            raise ValueError(f"fact {fact.id} references the wrong employer/system")
    for metric in canonical.metrics:
        if system_pairs.get(metric.system_id) != metric.employer_id:
            raise ValueError(f"metric {metric.id} references the wrong employer/system")

    for employer in canonical.employers:
        for boundary_id in employer.boundary_ids:
            if boundary_id not in boundary_by_id:
                raise ValueError(f"unknown employer boundary: {boundary_id}")
        for system in employer.systems:
            expected = employer.id
            for fact_id in (
                system.problem_fact_ids
                + system.input_fact_ids
                + system.action_fact_ids
                + system.output_fact_ids
                + system.outcome_fact_ids
                + system.status_fact_ids
            ):
                fact = fact_by_id.get(fact_id)
                if fact is None or fact.system_id != system.id or fact.employer_id != expected:
                    raise ValueError(f"fact {fact_id} does not belong to system {system.id}")
            for metric_id in system.metric_ids:
                metric = metric_by_id.get(metric_id)
                if metric is None or metric.system_id != system.id or metric.employer_id != expected:
                    raise ValueError(f"metric {metric_id} does not belong to system {system.id}")
            for boundary_id in system.boundary_ids:
                if boundary_id not in boundary_by_id:
                    raise ValueError(f"unknown system boundary: {boundary_id}")
            for accomplishment in system.accomplishments:
                if accomplishment.system_id != system.id:
                    raise ValueError(f"accomplishment {accomplishment.id} crosses systems")
                for fact_id in accomplishment.fact_ids:
                    fact = fact_by_id.get(fact_id)
                    if fact is None or fact.system_id != system.id:
                        raise ValueError(f"accomplishment {accomplishment.id} crosses fact systems")
                for metric_id in accomplishment.metric_ids:
                    metric = metric_by_id.get(metric_id)
                    if metric is None or metric.system_id != system.id:
                        raise ValueError(f"accomplishment {accomplishment.id} crosses metric systems")
                for boundary_id in accomplishment.boundary_ids:
                    if boundary_id not in boundary_by_id:
                        raise ValueError(f"unknown accomplishment boundary: {boundary_id}")

    if canonical.prototype_pattern.metric_ids:
        raise ValueError("prototype cannot claim an employer metric")
    return canonical


def load_canonical_v3(path: Path) -> CanonicalV3:
    data = load_yaml_unique(path)
    if not isinstance(data, dict):
        raise ValueError("canonical YAML root must be an object")
    return validate_canonical_v3(data)


def _references(canonical: CanonicalV3) -> list[SourceRef]:
    refs = []
    refs.extend(ref for fact in canonical.facts for ref in fact.source_refs)
    refs.extend(ref for metric in canonical.metrics for ref in metric.source_refs)
    refs.extend(ref for boundary in canonical.boundaries for ref in boundary.source_refs)
    refs.extend(
        ref
        for employer in canonical.employers
        for system in employer.systems
        for ref in system.source_refs
    )
    return refs


def check_migration(canonical: CanonicalV3, archive_path: Path) -> dict:
    raw = archive_path.read_bytes()
    archive_hash = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    invalid = []
    for ref in _references(canonical):
        actual = "\n".join(lines[ref.start_line - 1:ref.end_line]).strip()
        if (
            ref.archive_sha256.lower() != archive_hash.lower()
            or ref.end_line < ref.start_line
            or ref.end_line > len(lines)
            or actual != ref.quote.strip()
        ):
            invalid.append({
                "start_line": ref.start_line,
                "end_line": ref.end_line,
                "expected_hash": ref.archive_sha256,
            })

    covered = set()
    invalid_migration = []
    for entry in canonical.migration:
        if entry.end_line < entry.start_line or entry.end_line > len(lines):
            invalid_migration.append(entry.model_dump())
            continue
        covered.update(range(entry.start_line, entry.end_line + 1))
    unmapped = [
        index
        for index, line in enumerate(lines, 1)
        if line.strip() and index not in covered
    ]
    result = {
        "archive_sha256": archive_hash,
        "expected_sha256": canonical.source_archive_sha256,
        "invalid_source_refs": invalid,
        "invalid_migration_entries": invalid_migration,
        "unmapped_nonblank_lines": unmapped,
    }
    result["complete"] = (
        archive_hash.lower() == canonical.source_archive_sha256.lower()
        and not invalid
        and not invalid_migration
        and not unmapped
    )
    return result
