from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    # YAML represents enum values as strings. Pydantic still validates every
    # field and forbids unknown keys, while allowing those strings to become
    # their declared enum members.
    model_config = ConfigDict(extra="forbid")


class SourceRef(StrictModel):
    archive_sha256: str = Field(pattern=r"^[A-Fa-f0-9]{64}$")
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    quote: str = Field(min_length=1)


class FactKind(str, Enum):
    problem = "problem"
    input = "input"
    action = "action"
    output = "output"
    outcome = "outcome"
    status = "status"


class MetricStatus(str, Enum):
    achieved = "achieved"
    target = "target"
    derived = "derived"


class Fact(StrictModel):
    id: str
    employer_id: str
    system_id: str
    kind: FactKind
    text: str
    source_refs: list[SourceRef] = Field(min_length=1)


class Metric(StrictModel):
    id: str
    employer_id: str
    system_id: str
    display_text: str
    meaning: str
    status: MetricStatus
    source_refs: list[SourceRef] = Field(min_length=1)


class Boundary(StrictModel):
    id: str
    scope_ids: list[str] = Field(min_length=1)
    text: str
    source_refs: list[SourceRef] = Field(min_length=1)


class Accomplishment(StrictModel):
    id: str
    system_id: str
    purpose: str
    fact_ids: list[str] = Field(min_length=1)
    metric_ids: list[str] = Field(default_factory=list)
    boundary_ids: list[str] = Field(default_factory=list)


class SystemRecord(StrictModel):
    id: str
    narrative: str
    source_refs: list[SourceRef] = Field(min_length=1)
    problem_fact_ids: list[str] = Field(default_factory=list)
    input_fact_ids: list[str] = Field(default_factory=list)
    action_fact_ids: list[str] = Field(default_factory=list)
    output_fact_ids: list[str] = Field(default_factory=list)
    outcome_fact_ids: list[str] = Field(default_factory=list)
    metric_ids: list[str] = Field(default_factory=list)
    boundary_ids: list[str] = Field(default_factory=list)
    status_fact_ids: list[str] = Field(default_factory=list)
    accomplishments: list[Accomplishment] = Field(min_length=1)


class EmployerRecord(StrictModel):
    id: str
    company: str
    titles: list[str] = Field(min_length=1)
    period: str
    status_text: str
    boundary_ids: list[str] = Field(default_factory=list)
    systems: list[SystemRecord] = Field(min_length=1)


class EducationRecord(StrictModel):
    degree: str
    school: str
    year: str


class CanonicalPolicies(StrictModel):
    stack_retrofit: Literal["functional"]
    max_bullets_per_employer: Literal[4]
    include_independent_project: Literal[True]


class PrototypePattern(StrictModel):
    statement: str
    local_scope: str
    publication_status: str
    source_session_note: str
    restrictions: list[str] = Field(min_length=1)
    metric_ids: list[str] = Field(default_factory=list)


class MigrationEntry(StrictModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    destination_ids: list[str] = Field(default_factory=list)
    disposition: Literal["structured", "archived", "superseded"]


class CanonicalV3(StrictModel):
    schema_version: Literal[3]
    source_archive: str
    source_archive_sha256: str = Field(pattern=r"^[A-Fa-f0-9]{64}$")
    profile: dict[str, str]
    education: list[EducationRecord] = Field(min_length=2)
    identity: dict[str, Any]
    administrative: dict[str, Any]
    policies: CanonicalPolicies
    employers: list[EmployerRecord] = Field(min_length=1)
    facts: list[Fact] = Field(min_length=1)
    metrics: list[Metric] = Field(default_factory=list)
    boundaries: list[Boundary] = Field(default_factory=list)
    prototype_pattern: PrototypePattern
    migration: list[MigrationEntry] = Field(min_length=1)


class SkillKind(str, Enum):
    LANGUAGE = "LANGUAGE"
    INTERFACE = "INTERFACE"
    FRAMEWORK_LIBRARY = "FRAMEWORK_LIBRARY"
    MODEL = "MODEL"
    PROVIDER = "PROVIDER"
    CLOUD_PLATFORM_SERVICE = "CLOUD_PLATFORM_SERVICE"
    DATABASE_STORAGE = "DATABASE_STORAGE"
    AUTOMATION_ORCHESTRATION = "AUTOMATION_ORCHESTRATION"
    DEPLOYMENT_TOOL = "DEPLOYMENT_TOOL"
    DEVELOPMENT_TOOL = "DEVELOPMENT_TOOL"
    METHOD_ARCHITECTURE = "METHOD_ARCHITECTURE"
    DOMAIN = "DOMAIN"
    UNSPECIFIED_FAMILY = "UNSPECIFIED_FAMILY"
    UNCERTAIN = "UNCERTAIN"


class Component(StrictModel):
    id: str
    requirement_id: str
    text: str
    quote: str
    priority: str


class RequirementV3(StrictModel):
    id: str
    text: str
    quote: str
    priority: str
    component_ids: list[str]


class SkillItem(StrictModel):
    id: str
    exact_term: str
    jd_quote: str
    kind: SkillKind
    display_group: str
    centrality: str
    display_text: str
    aliases: list[str] = Field(default_factory=list)


class SkillGroup(StrictModel):
    id: str
    label: str
    item_ids: list[str] = Field(min_length=1)


class JobV3(StrictModel):
    company: str
    role: str
    location: str
    thesis: str
    requirements: list[RequirementV3] = Field(min_length=1)
    components: list[Component] = Field(min_length=1)
    stack_items: list[SkillItem] = Field(default_factory=list)


class DecisionCase(StrictModel):
    id: str
    node_id: str
    dimension: str
    state: dict[str, Any]
    question: str
    criteria: dict[str, str]
    dependency_hash: str


class Issue(StrictModel):
    code: str
    node_ids: list[str] = Field(min_length=1)
    target_ids: list[str] = Field(default_factory=list)
    instruction: str
    decision_ids: list[str] = Field(default_factory=list)
    unresolved: bool = True
