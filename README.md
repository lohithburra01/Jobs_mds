# Local application harness

Paste a job description into PowerShell. The harness writes a tailored resume and cover letter, saves their JSON, builds two PDFs, and writes a readable coverage report. Jev chooses and checks; the writer creates prose. Writing v3 uses one coherent initial creation call plus at most two shared targeted repair rounds. It is a working experiment, not a guarantee of ATS passage, recruiter response, or interview outcomes.

## Start on this computer

The local API key is already configured. From this folder:

```powershell
$python = 'C:\Users\91910\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python -m harness new
```

Paste the JD, then type `/done` on a separate line. Alternatively:

```powershell
& $python -m harness new --jd examples\stibo.jd.md
```

The terminal shows progress and the saved job folder. Normal runs do not ask you to approve bullets or confirm JD tools. This is a command-line program, not a chat agent. Errors and unresolved decisions stop with saved progress and `REVIEW_REQUIRED`; optional missing contacts are omitted.

## Setup on another computer

Use Python 3.11 or later. Keep this folder's Markdown sources, policy, and config together:

```powershell
py -m pip install -e .
Copy-Item .env.example .env
```

Put the OpenRouter key in `.env` locally. Then run `python -m harness new` from this folder. The runtime calls OpenRouter directly and does not require Codex. Source excerpts and the JD are sent to the configured providers; execution and saved files remain local. API costs apply.

`config.json` selects the writer and Jev models. V3 allows one complete initial draft plus two shared repair rounds and at most 80 HTTP attempts per job. Invalid responses and transient network failures consume the same budget. A repair rewrites only IDs named by a specific issue; passing text is retained. Stage usage and pending writer responses are persisted so interruption and resume preserve attempts, work, and cost attribution.

## Open, resume, or render a saved job

```powershell
& $python -m harness inspect jobs\stibo-jd-20260920T084255794382Z
& $python -m harness resume jobs\stibo-jd-20260920T084255794382Z
& $python -m harness render jobs\stibo-jd-20260920T084255794382Z
```

`resume` uses saved inputs, cached responses and remaining repair attempts. It does not reset exhausted attempts. Code changes that affect generation can invalidate affected blocks; edit policies/config before starting a **new** experiment if comparing versions.

`render` rebuilds PDFs from `application.json` and `profile.json` without loading credentials or calling an API. Manual prose edits are labeled `MANUALLY_MODIFIED`, not automatically approved by earlier Jev checks. It creates a new render folder, preserving previous PDFs.

Each job contains:

- `application.json`: existing public renderer schema, with generated resume and letter.
- `coverage.md` and `coverage.json`: every JD component, skill classification/group, employer allocation, project scope, unresolved issue, local PDF check, and usage count.
- `profile.json`: header/contact details.
- `renders/`: resume and cover-letter PDF revisions.
- `run.json`: progress, block revisions, failures and reported API cost.
- `decision_trace.json`: Jev choices and their recorded probabilities.
- `chat_context.md`: JD, output and selected source context for later discussion.
- `inputs/`, `requests/`, `responses/`: source snapshots and reproducible request records. Keys are excluded.

## What the status means

`ACCEPTED_EXPERIMENTAL` means every required current child and parent decision passed, every core work component is explicit, and the final PDFs passed local layout checks. Jev judgments have not been calibrated against hiring outcomes.

`REVIEW_REQUIRED` means PDFs were produced but at least one text or layout check failed. Inspect them anyway: a failed draft is useful evidence about what needs improving. The process exits with code 2. `STOPPED` means an error interrupted execution; inspect the saved folder and resume after fixing the cause. Ordinary errors exit with code 1.

The historical v1 Stibo run produced one-page PDFs for about $0.039, but failed readability and three block checks. See `FIRST-RUN.md`. Writing v2 was then tested on fresh Stibo and McKesson jobs. Both produced mechanically valid PDFs, exhausted two repair rounds and remained `REVIEW_REQUIRED`. See `WRITING-V2-RESULTS.md` and the blind A/B folders before deciding whether either version is worth sending.

## Current limits

- V3 has passed offline structural, hierarchy, resume-layout, interruption, and compatibility tests. It has not yet completed an authorized paid quality run.
- `canonical.yaml` is the active source; the archived Markdown is provenance only.
- Skills use item -> group -> whole-section checks. Experience uses bullet -> employer -> whole-section checks. A parent PASS never overrides a failed child.
- Experience has no global bullet cap. Each employer has at most four, all four employers remain, and actual one-page ReportLab measurement selects the strongest fitting subset.
- Every v3 resume includes one JD-relevant independent local/GitHub prototype with no invented date, URL, employer metric, or company scale.
- Missing email and links are omitted. Automated PDF checks cover page count, selectable text, and fixed 10-point body type; the offline v3 fixture was also visually inspected.

## One-shot comparison

For a completed writing-v2 job:

```powershell
& $python -m scripts.compare_writing --job jobs\JOB-FOLDER
```

This makes exactly one writer creation call from the saved inputs, writes to a separate `comparisons/one-shot-*` directory and does not change the harness result. It incurs API cost. The control is rendered with the same profile and template but receives no harness-generated prose or repair feedback.

## Offline tests

```powershell
& $python -m unittest discover -s tests -v
```

Tests make no paid calls. `.env`, job folders and temporary renders are ignored by Git. No application is submitted automatically.
