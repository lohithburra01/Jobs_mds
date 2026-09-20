# Renderer implementation report

Implemented the isolated Task 2 renderer in `renderer/build.py` and
`harness/rendering.py` while preserving the existing application JSON shape.
The layout follows the supplied ReportLab renderer's section structure, but
all identity/contact fields now come from the passed profile and resume body
styles are at least 10 pt.

## Behavior covered

- Required profile fields: name, location, phone.
- Optional profile fields: email, LinkedIn URL, GitHub URL; omitted values do
  not appear in either PDF.
- Plain application/profile strings are escaped before ReportLab markup, so
  ampersands and angle brackets do not break rendering or become markup.
- PDFs are staged in the requested output directory and inspected with
  `pypdf` for page count and selectable text.
- Multi-page documents are returned with failed QA checks rather than being
  accepted or silently shrunk.
- Invalid public JSON/profile shapes fail before PDF creation with a field-
  specific `ValueError`.

## Tests

The renderer tests use the real ReportLab and pypdf implementations. The
initial run failed because `harness.rendering` did not exist, establishing the
test-first red state. After implementation:

```text
python -m unittest discover -s tests -p 'test_rendering.py' -v
Ran 5 tests
OK

python -m unittest discover -s tests -v
Ran 15 tests
OK
```

The cases cover profile-sourced headers, absence of old hardcoded contact
details, literal ampersands, optional links, selectable text in both files,
one-page success, explicit oversized-resume failure, the 10 pt minimum result
contract, and clear validation failures without partial PDFs.

A representative render using the supplied Rydoo application JSON produced a
one-page resume and one-page cover letter with selectable text. Both pages
were rasterized with Poppler and inspected: headings, rules, dates, contact
links, bullets, wrapping, margins, and the closing were visible without
clipping or overlap. `pypdf` content inspection reported 10 pt for the sampled
resume summary and bullet text. Poppler emitted standard-font lookup warnings
for `Symbol`/`ArialUnicode` while rasterizing, but neither rendered page showed
a missing glyph or black box.

## Remaining QA limits

Page count and text extraction do not detect clipping, awkward line breaks,
or visually unbalanced whitespace. The primary agent should inspect PNG
renders of the first real resume and cover letter. The renderer reports cover
letters over one page as failed as well; text repair remains a pipeline
decision. The current renderer supports the settled empty `projects` array
and rejects populated projects so the public prototype shape cannot drift.
