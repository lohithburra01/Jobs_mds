"""Offline application rendering adapter and PDF quality checks."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.platypus.doctemplate import LayoutError

from renderer.build import MINIMUM_BODY_FONT_PT, build_cover_letter, build_resume


_PROFILE_REQUIRED = {"name", "location", "phone"}
_PROFILE_OPTIONAL = {"email", "linkedin", "github"}


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_exact_keys(value: dict[str, Any], field: str, keys: set[str]) -> None:
    missing = sorted(keys - set(value))
    extra = sorted(set(value) - keys)
    if missing:
        raise ValueError(f"{field}.{missing[0]} is required")
    if extra:
        raise ValueError(f"{field} contains unsupported field: {extra[0]}")


def _require_text(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} must not be empty")
    return value


def _require_list(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    if not allow_empty and not value:
        raise ValueError(f"{field} must not be empty")
    return value


def _validate_profile(profile: Any) -> dict[str, str]:
    values = _require_mapping(profile, "profile")
    allowed = _PROFILE_REQUIRED | _PROFILE_OPTIONAL
    missing = sorted(_PROFILE_REQUIRED - set(values))
    extra = sorted(set(values) - allowed)
    if missing:
        raise ValueError(f"profile.{missing[0]} is required")
    if extra:
        raise ValueError(f"profile contains unsupported field: {extra[0]}")
    validated: dict[str, str] = {}
    for key in _PROFILE_REQUIRED:
        validated[key] = _require_text(values[key], f"profile.{key}")
    for key in _PROFILE_OPTIONAL:
        if key in values and values[key] is not None:
            text = _require_text(values[key], f"profile.{key}")
            validated[key] = text
    return validated


def _validate_application(application: Any) -> dict[str, Any]:
    root = _require_mapping(application, "application")
    _require_exact_keys(root, "application", {"company_name", "resume", "cover_letter"})
    _require_text(root["company_name"], "company_name")

    resume = _require_mapping(root["resume"], "resume")
    _require_exact_keys(
        resume,
        "resume",
        {"summary", "skills", "experience", "projects", "education"},
    )
    _require_text(resume["summary"], "resume.summary")

    skills = _require_list(resume["skills"], "resume.skills")
    for index, skill_value in enumerate(skills):
        field = f"resume.skills[{index}]"
        skill = _require_mapping(skill_value, field)
        _require_exact_keys(skill, field, {"label", "value"})
        _require_text(skill["label"], f"{field}.label")
        _require_text(skill["value"], f"{field}.value")

    experience_entries = _require_list(resume["experience"], "resume.experience")
    for index, experience_value in enumerate(experience_entries):
        field = f"resume.experience[{index}]"
        experience = _require_mapping(experience_value, field)
        _require_exact_keys(
            experience, field, {"title", "company", "period", "bullets"}
        )
        for key in ("title", "company", "period"):
            _require_text(experience[key], f"{field}.{key}")
        bullets = _require_list(experience["bullets"], f"{field}.bullets")
        for bullet_index, bullet in enumerate(bullets):
            _require_text(bullet, f"{field}.bullets[{bullet_index}]")

    projects = _require_list(resume["projects"], "resume.projects", allow_empty=True)
    if len(projects) > 1:
        raise ValueError("resume.projects may contain at most one project")
    for index, project_value in enumerate(projects):
        field = f"resume.projects[{index}]"
        project = _require_mapping(project_value, field)
        _require_exact_keys(project, field, {"name", "period", "bullets"})
        _require_text(project["name"], f"{field}.name")
        _require_text(project["period"], f"{field}.period", allow_empty=True)
        bullets = _require_list(project["bullets"], f"{field}.bullets")
        if len(bullets) != 2:
            raise ValueError(f"{field}.bullets must contain exactly two items")
        for bullet_index, bullet in enumerate(bullets):
            _require_text(bullet, f"{field}.bullets[{bullet_index}]")

    education_entries = _require_list(resume["education"], "resume.education")
    for index, education_value in enumerate(education_entries):
        field = f"resume.education[{index}]"
        education = _require_mapping(education_value, field)
        _require_exact_keys(education, field, {"degree", "school", "year"})
        for key in ("degree", "school", "year"):
            _require_text(education[key], f"{field}.{key}")

    cover_letter = _require_mapping(root["cover_letter"], "cover_letter")
    _require_exact_keys(
        cover_letter,
        "cover_letter",
        {"date", "company_address", "salutation", "paragraphs"},
    )
    _require_text(cover_letter["date"], "cover_letter.date")
    _require_text(
        cover_letter["company_address"],
        "cover_letter.company_address",
        allow_empty=True,
    )
    _require_text(cover_letter["salutation"], "cover_letter.salutation")
    paragraphs = _require_list(cover_letter["paragraphs"], "cover_letter.paragraphs")
    for index, paragraph in enumerate(paragraphs):
        _require_text(paragraph, f"cover_letter.paragraphs[{index}]")
    return root


def _filename_component(value: str, fallback: str) -> str:
    component = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return component or fallback


def _inspect_pdf(path: Path) -> tuple[int, str]:
    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as error:
        raise ValueError(f"could not inspect rendered PDF {path.name}: {error}") from error
    if page_count < 1:
        raise ValueError(f"rendered PDF {path.name} contains no pages")
    return page_count, text


def render_application(
    application: dict, profile: dict, out_dir: Path
) -> dict[str, Any]:
    """Render and inspect one application without any network or model calls.

    A resume or letter exceeding one page is still returned so the caller can
    repair the source text.  ``checks['passed']`` is false in that case.
    """
    validated_application = _validate_application(application)
    validated_profile = _validate_profile(profile)
    output_directory = Path(out_dir)
    if output_directory.exists() and not output_directory.is_dir():
        raise ValueError(f"out_dir is not a directory: {output_directory}")
    output_directory.mkdir(parents=True, exist_ok=True)

    person = _filename_component(validated_profile["name"], "Candidate")
    company = _filename_component(validated_application["company_name"], "Application")
    resume_path = output_directory / f"{person}_{company}.pdf"
    cover_letter_path = output_directory / f"{person}_{company}_CoverLetter.pdf"
    nonce = uuid.uuid4().hex
    temporary_resume = output_directory / f".{nonce}.resume.tmp.pdf"
    temporary_letter = output_directory / f".{nonce}.cover_letter.tmp.pdf"

    try:
        build_resume(
            validated_application["resume"], validated_profile, temporary_resume
        )
        build_cover_letter(
            validated_application["cover_letter"],
            validated_profile,
            temporary_letter,
        )
        resume_pages, resume_text = _inspect_pdf(temporary_resume)
        letter_pages, letter_text = _inspect_pdf(temporary_letter)
        os.replace(temporary_resume, resume_path)
        os.replace(temporary_letter, cover_letter_path)
    except LayoutError as error:
        raise ValueError(f"PDF layout failed: {error}") from error
    except (OSError, ValueError):
        raise
    except Exception as error:
        raise ValueError(f"PDF rendering failed: {error}") from error
    finally:
        for temporary_path in (temporary_resume, temporary_letter):
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass

    resume_selectable = bool(resume_text.strip())
    letter_selectable = bool(letter_text.strip())
    checks = {
        "resume_one_page": resume_pages == 1,
        "cover_letter_one_page": letter_pages == 1,
        "resume_selectable_text": resume_selectable,
        "cover_letter_selectable_text": letter_selectable,
        "minimum_body_font_pt": MINIMUM_BODY_FONT_PT,
        "passed": (
            resume_pages == 1
            and letter_pages == 1
            and resume_selectable
            and letter_selectable
        ),
    }
    return {
        "resume": str(resume_path),
        "cover_letter": str(cover_letter_path),
        "page_counts": {"resume": resume_pages, "cover_letter": letter_pages},
        "extracted_text": {"resume": resume_text, "cover_letter": letter_text},
        "checks": checks,
    }
