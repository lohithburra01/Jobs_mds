from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TERMINAL_STATES = {"COMPLETED", "BLOCKED", "DESIGN_CONFLICT", "FAILED", "TIMED_OUT", "STOPPED"}


def _literal_relative(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not value or path.is_absolute() or ".." in path.parts or any(c in value for c in "*?[]"):
        raise ValueError("path must be a literal relative path without '..' or glob characters")
    return path.as_posix().rstrip("/")


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    evidence_paths: list[str] = Field(default_factory=list)

    @field_validator("evidence_paths")
    @classmethod
    def paths_are_relative(cls, paths):
        return [_literal_relative(path) for path in paths]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    workspace: Path
    allowed_paths: list[str] = Field(min_length=1)
    protected_paths: list[str] = Field(default_factory=list)
    model: str = "gpt-5.6-sol"
    deadline_seconds: int = Field(default=1200, gt=0)
    verification_commands: list[list[str]] = Field(default_factory=list)
    brief_file: Path | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    semantic_review: bool = False

    @field_validator("allowed_paths", "protected_paths")
    @classmethod
    def paths_are_relative(cls, paths):
        return [_literal_relative(path) for path in paths]

    @field_validator("verification_commands")
    @classmethod
    def commands_are_argv(cls, commands):
        if any(not command or any(not isinstance(arg, str) or not arg for arg in command) for command in commands):
            raise ValueError("verification commands must be nonempty argument arrays")
        return commands

    @model_validator(mode="after")
    def workspace_exists(self):
        self.workspace = self.workspace.resolve()
        if not self.workspace.is_dir():
            raise ValueError("workspace must be an existing directory")
        if self.brief_file is not None:
            self.brief_file = self.brief_file.resolve()
            if not self.brief_file.is_file():
                raise ValueError("brief_file must be an existing file")
        return self


class WorkerReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["COMPLETED_WITH_EVIDENCE", "BLOCKED", "DESIGN_CONFLICT"]
    summary: str = Field(min_length=1)
    changed_files: list[str]
    evidence: list[str]


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: str
    run: str
    event: str
    status: str
    details: str = ""
