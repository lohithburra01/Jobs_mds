from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

Text = Annotated[str, Field(strict=True, min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Skill(StrictModel):
    label: Text
    value: Text


class Experience(StrictModel):
    title: Text
    company: Text
    period: Text
    bullets: list[Text] = Field(min_length=1, max_length=4)


class Education(StrictModel):
    degree: Text
    school: Text
    year: Text


class Resume(StrictModel):
    summary: Text
    skills: list[Skill] = Field(min_length=1)
    experience: list[Experience] = Field(min_length=4, max_length=4)
    projects: list = Field(max_length=0)
    education: list[Education] = Field(min_length=2, max_length=2)


class CoverLetter(StrictModel):
    date: Text
    company_address: str
    salutation: Text
    paragraphs: list[Text] = Field(min_length=1, max_length=3)


class Application(StrictModel):
    company_name: Text
    resume: Resume
    cover_letter: CoverLetter


class Requirement(StrictModel):
    text: Text
    quote: Text


class StackTerm(StrictModel):
    term: Text
    quote: Text


class JobDraft(StrictModel):
    company: Text
    role: Text
    location: str
    thesis: Text
    requirements: list[Requirement] = Field(min_length=3, max_length=16)
    stack: list[StackTerm] = Field(max_length=50)


class WrittenBlocks(StrictModel):
    blocks: dict[str, Text]
