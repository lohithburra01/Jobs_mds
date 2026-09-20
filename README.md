# Local application harness

Paste a job description into PowerShell. The harness writes a tailored resume and cover letter, saves their JSON, and builds two PDFs. Jev chooses and checks; the writer produces prose. Writing v2 checks the complete application and repairs only diagnosed blocks, with one initial attempt plus at most two repairs per block. It is a working experiment, not a demonstrated improvement over a good one-shot prompt or human writing.

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

The terminal shows progress and the saved job folder. Normal runs do not ask you to approve bullets. This is a command-line program, not a chat agent. There is currently **no interactive missing-fact question screen**: errors stop with saved progress; optional missing contacts are omitted. The question-and-answer interface in the earlier design is not implemented.

## Setup on another computer

Use Python 3.11 or later. Keep this folder's Markdown sources, policy, and config together:

```powershell
py -m pip install -e .
Copy-Item .env.example .env
```

Put the OpenRouter key in `.env` locally. Then run `python -m harness new` from this folder. The runtime calls OpenRouter directly and does not require Codex. Source excerpts and the JD are sent to the configured providers; execution and saved files remain local. API costs apply.

`config.json` selects the writer and Jev models. The prototype allows one initial draft plus two repairs per block and at most 80 HTTP attempts per job. Invalid classifier responses and transient network failures also consume the HTTP budget. A repair rewrites only blocks with a specific local or relationship issue; passing blocks are retained. Stage usage baselines are persisted before calls so interruption and resume preserve cost attribution.

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
- `profile.json`: header/contact details.
- `renders/`: resume and cover-letter PDF revisions.
- `run.json`: progress, block revisions, failures and reported API cost.
- `decision_trace.json`: Jev choices and their recorded probabilities.
- `chat_context.md`: JD, output and selected source context for later discussion.
- `inputs/`, `requests/`, `responses/`: source snapshots and reproducible request records. Keys are excluded.

## What the status means

`ACCEPTED_EXPERIMENTAL` means the implemented checks passed. Jev judgments have not been calibrated against human-rated examples, so this is not a guarantee of writing quality or interview outcomes.

`REVIEW_REQUIRED` means PDFs were produced but at least one text or layout check failed. Inspect them anyway: a failed draft is useful evidence about what needs improving. The process exits with code 2. `STOPPED` means an error interrupted execution; inspect the saved folder and resume after fixing the cause. Ordinary errors exit with code 1.

The historical v1 Stibo run produced one-page PDFs for about $0.039, but failed readability and three block checks. See `FIRST-RUN.md`. Writing v2 was then tested on fresh Stibo and McKesson jobs. Both produced mechanically valid PDFs, exhausted two repair rounds and remained `REVIEW_REQUIRED`. See `WRITING-V2-RESULTS.md` and the blind A/B folders before deciding whether either version is worth sending.

## Current limits

- Two live v2 runs still ended with abstract summary/letter language; the McKesson letter also repeated its proof example. The current repair prompts did not reliably resolve those issues within the fixed budget.
- The planner uses a fixed allocation across four employers and the first available title variant. Harness skills are currently one flat list.
- The original engine document is snapshotted for reference. Its full instructions are **not** automatically executable policy; only the implemented rules apply.
- Missing email and links are omitted. Confirm these before using an application.
- Automated PDF checks cover page count and selectable text, not every visual defect. The first real PDFs were also inspected as images.
- Three attached JDs are saved as fixtures. Stibo and McKesson have paired one-shot controls; these are controlled writer baselines, not calibrated human-quality scores or a chat-session benchmark.

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
