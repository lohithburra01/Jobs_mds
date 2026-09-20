# Writing v2 experiment results

Date: 20 September 2026

This experiment compares the bounded v2 harness with a single writer call. Both sides received the same saved JD, canonical evidence, writing plan, profile, date and renderer. The control received no harness prose, diagnoses or repairs. The comparison measures writing orchestration only; it is not a comparison with an independently written human resume.

## Stibo Systems

- Harness job: `jobs/stibo-jd-20260920T151708861102Z`
- Harness result: `REVIEW_REQUIRED`; 44 HTTP attempts; $0.044793662 provider-reported cost; two repair rounds.
- Complete-document checks: consistency PASS, readability PASS, coverage PASS.
- Remaining diagnosed blocks: abstract language in the summary, opening, closing and Think Round bullet.
- One-shot control: one writer call; $0.01258445; both PDFs passed page-count, selectable-text and minimum-font checks.
- Both pairs were visually inspected as page images. No clipping, overlap, missing glyphs or unreadable text was found.
- Historical accounting note: the harness stopped once on an oversized assessment request and was resumed after the batching fix. Its total call/cost counters are complete, but its saved stage rows omit the successful initial-writing calls made before that interruption. Do not sum those rows as the run total.

## McKesson

- Harness job: `jobs/mckesson-jd-20260920T152242318211Z`
- Harness result: `REVIEW_REQUIRED`; 43 HTTP attempts; $0.044369466 provider-reported cost; two repair rounds.
- Complete-document checks: consistency PASS, readability PASS, coverage PASS.
- Remaining diagnosed blocks: abstract language in the summary, opening, closing, Think Round bullet and Cognizant bullet; the closing did the wrong paragraph job; the opening repeated the proof paragraph.
- One-shot control: one writer call; $0.01170511; both PDFs passed page-count, selectable-text and minimum-font checks.
- Both pairs were visually inspected as page images. No clipping, overlap, missing glyphs or unreadable text was found. The harness cover letter is visibly underfilled and repeats its main example.

## What the result establishes

The harness is resumable, bounded, renders usable one-page documents, preserves passing blocks during repairs and identifies real document-level problems. It did not produce an application-ready result in either live case. Both runs exhausted their two repair rounds and remained `REVIEW_REQUIRED`.

The one-shot controls cost roughly one quarter as much as the complete harness runs. They passed only mechanical PDF checks; they were not granted a semantic pass. Human blind review is required before deciding whether the harness writing is better, worse or merely different.

## Blind review

Each case has `comparisons/blind-review/` containing A and B resume/letter pairs plus plain review questions. The randomized mapping is stored separately in `comparisons/blind-review-mapping.json`. Choose A, B, neither or tie before opening the mapping.

Review each pair on five points:

1. Is the candidate's main value obvious within 15 seconds?
2. Can you understand what work changed and why it mattered?
3. Does the technology fit the job without reading like a keyword dump?
4. Does the cover letter add a concrete reason to interview the candidate?
5. Which pair would you actually send: A, B, neither or tie?

## Implementation verification

Writing v2 adds single-purpose blocks, evidence-specificity ranking, one reserved cover-letter proof, document-level issue and relationship checks, deterministic repair targeting, persistent three-attempt budgets, version isolation and a one-call comparison runner. Stage accounting now persists its baseline before calls so future interrupted stages retain pre-interruption usage. The live outputs were preserved and were not edited after generation.
