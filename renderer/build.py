"""ReportLab builders for the public application JSON document shape.

All values passed to this module are plain text.  This module owns the
plain-text-to-ReportLab-markup boundary and escapes values before wrapping
the small amount of markup used by the templates.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BLACK = colors.HexColor("#111111")
DARK = colors.HexColor("#222222")
GREY = colors.HexColor("#666666")
LINK_BLUE = "#1155CC"
MINIMUM_BODY_FONT_PT = 10.0


def _plain(value: str) -> str:
    """Normalize troublesome dashes and escape plain text for Paragraph."""
    normalized = value.replace("\N{EM DASH}", "-").replace("\N{EN DASH}", "-")
    return html.escape(normalized, quote=True)


def _with_breaks(value: str) -> str:
    return "<br/>".join(_plain(line) for line in value.splitlines())


def _styles() -> Any:
    styles = getSampleStyleSheet()

    def add(name: str, base_name: str = "Normal", **kwargs: Any) -> None:
        styles.add(ParagraphStyle(name, parent=styles[base_name], **kwargs))

    add(
        "ResumeName",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    add(
        "ResumeContact",
        fontName="Helvetica",
        fontSize=8.5,
        leading=10,
        textColor=GREY,
        alignment=TA_CENTER,
        spaceAfter=5,
    )
    add(
        "ResumeSection",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=12,
        spaceBefore=5,
        spaceAfter=1,
        textColor=BLACK,
    )
    add(
        "ResumeBody",
        fontName="Helvetica",
        fontSize=MINIMUM_BODY_FONT_PT,
        leading=12,
        spaceAfter=2,
    )
    add(
        "ResumeBullet",
        fontName="Helvetica",
        fontSize=MINIMUM_BODY_FONT_PT,
        leading=12,
        leftIndent=10,
        firstLineIndent=-10,
        spaceAfter=1.5,
    )
    add(
        "ResumeItemHeading",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=11,
        spaceBefore=2,
    )
    add(
        "ResumeItemCompany",
        fontName="Helvetica-Oblique",
        fontSize=MINIMUM_BODY_FONT_PT,
        leading=11,
        textColor=DARK,
        spaceAfter=1,
    )
    add(
        "ResumeItemDate",
        fontName="Helvetica",
        fontSize=MINIMUM_BODY_FONT_PT,
        leading=11,
        alignment=TA_RIGHT,
    )
    add(
        "LetterName",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        spaceAfter=2,
    )
    add(
        "LetterContact",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=GREY,
        spaceAfter=20,
    )
    add(
        "LetterBody",
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )
    return styles


def _contact_markup(profile: dict[str, str]) -> str:
    parts = [_plain(profile["location"]), _plain(profile["phone"])]
    if profile.get("email"):
        parts.insert(1, _plain(profile["email"]))
    for key, label in (("linkedin", "LinkedIn"), ("github", "GitHub")):
        if profile.get(key):
            url = html.escape(profile[key], quote=True)
            parts.append(f'<a href="{url}"><font color="{LINK_BLUE}">{label}</font></a>')
    return " | ".join(parts)


def _section(story: list[Any], title: str, styles: Any) -> None:
    story.append(Paragraph(_plain(title), styles["ResumeSection"]))
    rule = Table([[""]], colWidths=[7.5 * inch], rowHeights=[1])
    rule.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 0.75, BLACK),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.extend((rule, Spacer(1, 2)))


def _dated_heading(title: str, period: str, styles: Any) -> Table:
    table = Table(
        [
            [
                Paragraph(_plain(title), styles["ResumeItemHeading"]),
                Paragraph(_plain(period), styles["ResumeItemDate"]),
            ]
        ],
        colWidths=[6.0 * inch, 1.5 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def build_resume(
    data: dict[str, Any], profile: dict[str, str], output_path: Path
) -> None:
    story = resume_flowables(data, profile)
    document = SimpleDocTemplate(str(output_path), **resume_document_options(profile))
    document.build(story)


def resume_document_options(profile: dict[str, str]) -> dict[str, Any]:
    """Single source for resume page geometry used by render and measurement."""
    return {
        "pagesize": letter,
        "leftMargin": 0.5 * inch,
        "rightMargin": 0.5 * inch,
        "topMargin": 0.5 * inch,
        "bottomMargin": 0.5 * inch,
        "compress": 0,
        "title": f'{profile["name"]} - Resume',
        "author": profile["name"],
    }


def resume_flowables(data: dict[str, Any], profile: dict[str, str]) -> list[Any]:
    """Build the exact story consumed by both PDF output and v3 fitting."""
    styles = _styles()
    story: list[Any] = [
        Paragraph(_plain(profile["name"]), styles["ResumeName"]),
        Paragraph(_contact_markup(profile), styles["ResumeContact"]),
    ]

    _section(story, "SUMMARY", styles)
    story.append(Paragraph(_plain(data["summary"]), styles["ResumeBody"]))

    _section(story, "CORE SKILLS", styles)
    for skill in data["skills"]:
        content = f'<b>{_plain(skill["label"])}:</b> {_plain(skill["value"])}'
        story.append(Paragraph(content, styles["ResumeBody"]))

    _section(story, "PROFESSIONAL EXPERIENCE", styles)
    for experience in data["experience"]:
        block: list[Any] = [
            _dated_heading(experience["title"], experience["period"], styles),
            Paragraph(_plain(experience["company"]), styles["ResumeItemCompany"]),
        ]
        block.extend(
            Paragraph(f"- {_plain(bullet)}", styles["ResumeBullet"])
            for bullet in experience["bullets"]
        )
        story.append(KeepTogether(block))

    if data["projects"]:
        _section(story, "KEY PROJECTS", styles)
        for project in data["projects"]:
            block = [_dated_heading(project["name"], project["period"], styles)]
            block.extend(
                Paragraph(f"- {_plain(bullet)}", styles["ResumeBullet"])
                for bullet in project["bullets"]
            )
            story.append(KeepTogether(block))

    _section(story, "EDUCATION", styles)
    for education in data["education"]:
        content = (
            f'<b>{_plain(education["degree"])}</b> - '
            f'{_plain(education["school"])} ({_plain(education["year"])})'
        )
        story.append(Paragraph(content, styles["ResumeBody"]))

    return story


def build_cover_letter(
    data: dict[str, Any], profile: dict[str, str], output_path: Path
) -> None:
    styles = _styles()
    story: list[Any] = [
        Paragraph(_plain(profile["name"]), styles["LetterName"]),
        Paragraph(_contact_markup(profile), styles["LetterContact"]),
        Paragraph(_plain(data["date"]), styles["LetterBody"]),
    ]
    if data["company_address"]:
        story.append(
            Paragraph(_with_breaks(data["company_address"]), styles["LetterBody"])
        )
    story.append(Paragraph(_plain(data["salutation"]), styles["LetterBody"]))
    story.extend(
        Paragraph(_plain(paragraph), styles["LetterBody"])
        for paragraph in data["paragraphs"]
    )
    story.extend(
        (
            Spacer(1, 12),
            Paragraph(
                f"Best regards,<br/><br/><b>{_plain(profile['name'])}</b>",
                styles["LetterBody"],
            ),
        )
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=1.1 * inch,
        rightMargin=1.1 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title=f'{profile["name"]} - Cover Letter',
        author=profile["name"],
    )
    document.build(story)
