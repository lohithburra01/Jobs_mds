# First real run: Stibo Systems

This file records the preserved writing-v1 run. Fresh writing-v2 runs and the controlled one-shot comparisons are documented in `WRITING-V2-RESULTS.md`; the v1 artifacts below were not rewritten.

Date: 20 September 2026. Job: AI Solutions Engineer. Input: `examples/stibo.jd.md`.

Saved job: `jobs/stibo-jd-20260920T084255794382Z`.

## Result

The harness completed real OpenRouter calls and produced both PDFs. Status: **REVIEW_REQUIRED**. Neither file is presented as application-ready.

- Resume: `renders/c04c47addac3/Lohith_Burra_Stibo_Systems.pdf` inside the job folder.
- Letter: `renders/c04c47addac3/Lohith_Burra_Stibo_Systems_CoverLetter.pdf`.
- 39 HTTP attempts, with total provider-reported cost **$0.038699848**. The separate provider smoke check is not included.
- Both PDFs have one page and selectable text. Resume body is at least 10 pt. Both rendered page images were inspected: no clipping, overlap, missing glyphs or broken section layout found. The letter uses the supplied template's justified text; it creates wider word spacing than left alignment.
- All eight resume bullets and four summary/letter blocks have saved revisions and check results.

## What failed

| Check | Actual result |
|---|---|
| Formula Dream first bullet | 35 words, exceeding its 32-word limit after three attempts |
| Letter opening | 76 words, exceeding its 75-word limit after three attempts |
| Letter closing | Jev marked clarity FAIL after three attempts |
| Whole application | Jev marked readability FAIL; consistency and planned requirement coverage passed |

The cover letter repeats the 200-client editorial pipeline in its first two paragraphs. Its closing is generic. The summary's “zero to one and one to ten” is harder to read than a direct description. The Cognizant bullet is vague about the actual change. These last observations are the developer's inspection of the experiment, not an additional model validator inside the harness.

The prototype's global check detects a problem but does not yet feed a specific repair back to the conflicting paragraphs. The block repair instructions repeat the failed rubric rather than identifying a precise change. That limits the value of repeated writing attempts and is the next writing-quality problem to solve. Increasing retry counts alone is not the answer.

## What this establishes

The local path from JD to saved prose, decisions and PDFs works with the real services. It preserves failed drafts instead of declaring success. It **does not establish better writing than chatting**, higher ATS acceptance or better interview results. No controlled same-model chat baseline or human-rated cross-JD comparison has been run.

The first extraction stopped because the writer capitalized the start of otherwise exact JD quotations. The parser was corrected to restore source casing while still rejecting changed wording; the run then resumed with saved requests. Initial code hashes therefore differ from the code used to complete it. The `executed-code/` snapshot in the job folder records completion-time code; subsequent interruption-recovery fixes are separate and have not changed these PDFs.

Preserve this first output when improving prompts or planning, so the next experiment can be compared against it. Do not silently rewrite it and call the rewrite the original harness result.
