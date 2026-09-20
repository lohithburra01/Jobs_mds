# PDF renderer

`harness.rendering.render_application(application, profile, out_dir)` is the
offline boundary for producing the resume and cover-letter PDFs. It accepts
the existing public application JSON shape and does not call a model, API, or
credential loader.

The profile object requires `name`, `location`, and `phone`. `email`,
`linkedin`, and `github` are optional. Missing optional values are omitted
from both document headers. The renderer never supplies contact details from
defaults or from the older source renderer.

The application object keeps this exact structure:

```text
company_name
resume
  summary
  skills[]: label, value
  experience[]: title, company, period, bullets[]
  projects: []
  education[]: degree, school, year
cover_letter
  date
  company_address
  salutation
  paragraphs[]
```

Input values are treated as plain text and escaped before they cross into
ReportLab paragraph markup. `company_address` is the only field where input
newlines become explicit line breaks. Resume body, bullet, company, and date
styles are 10 pt or larger. The cover-letter body is 10.5 pt. Contact lines
are secondary header text at 8.5 pt.

The return value is:

```python
{
    "resume": "path/to/resume.pdf",
    "cover_letter": "path/to/cover-letter.pdf",
    "page_counts": {"resume": 1, "cover_letter": 1},
    "extracted_text": {"resume": "...", "cover_letter": "..."},
    "checks": {
        "resume_one_page": True,
        "cover_letter_one_page": True,
        "resume_selectable_text": True,
        "cover_letter_selectable_text": True,
        "minimum_body_font_pt": 10.0,
        "passed": True,
    },
}
```

Both PDFs are built and inspected under temporary names in `out_dir` before
they replace their final filenames. A malformed application/profile or a
ReportLab build failure raises `ValueError` with the failing field or layout
stage. A document that renders successfully but exceeds one page is returned
with its page count and extracted text; its one-page check and aggregate
`passed` check are false. This lets the pipeline repair source text without
losing the diagnostic artifact or silently shrinking text below 10 pt.

The automated checks verify page count and that each PDF contains selectable
text. They do not prove visual polish, detect awkward page breaks, or measure
semantic writing quality. The final application run still needs rendered-page
inspection before release.
