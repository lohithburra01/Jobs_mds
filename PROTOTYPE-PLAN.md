# First live application run implementation plan

> For agentic workers: use subagent-driven-development for the isolated renderer task and review; keep pipeline integration with the primary agent. Track progress below.

Goal: run the supplied Stibo JD through real OpenRouter Jev decisions and a bounded writer, produce inspected resume/letter PDFs, and preserve trace/cost/repair records for comparison.

Spec: USER-WORKFLOW.md and the latest user corrections in MEMORY.md. User authorized starting and testing a first run on 2026-09-20. This authorizes the working prototype; it does not require implementing all future commands or providers before showing output.

Architecture: a small local Python package; exact Markdown evidence excerpts and inherited boundaries; fixed JSON decision definitions; OpenRouter adapters; deterministic evidence allocation; bounded writing/check/repair; cached calls and resumable checkpoints; existing ReportLab renderer adapted locally. The external application JSON stays unchanged. Jev handles semantic judgments; generative calls create only. Prototype acceptance uses categorical decisions with full probabilities recorded and is explicitly uncalibrated, never a production reliability claim.

Global constraints: preserve actual employers/dates/status/metrics; retrofit is settled and not a source of tool-confirmation questions; no automatic applications/submission; no secrets in Git/logs; no fabricated successful live run; preserve original source files and external renderer; minimum resume text 10pt; max two content repairs per block; max 80 HTTP attempts for a run; no silent approval when a gate fails. No model pricing or confidence guarantees.

## Task 1: Runtime, sources and request records (primary)

Files: harness/sources.py, harness/provider.py, harness/store.py, harness/models.py, tests/test_core.py, config.json, pyproject.toml.

Interfaces: load_canonical(path) returns profile/education/employers/evidence/global boundaries with exact source text; RunStore keeps atomic checkpoints and request cache; OpenRouter.create(task,payload) returns JSON; OpenRouter.decide(state,questions) returns validated Choice responses. Both go through bounded cached HTTP transport; templates and inputs appear in saved request records, credentials do not.

- [ ] Write failing tests for inherited source restrictions, escaped credentials in errors, cached request reuse and strict Jev answer validation.
- [ ] Run tests and observe intended missing-behavior failures.
- [x] Implement parsing, typed schemas, request caching/transport and local credential loading.
- [x] Verify tests; no network calls in unit tests.

## Task 2: Renderer adaptation (isolated subagent)

Files: renderer/build.py (copy adapted from supplied renderer), harness/rendering.py, tests/test_rendering.py. No shared edits to pipeline/provider/source files.

Interface: render_application(application: dict, profile: dict, out_dir: Path) -> dict with resume/cover_letter paths, page counts, extracted text and QA results. Raise ValueError on schema/layout problems. profile has name, location, phone and optional email/linkedin/github. Do not source omitted fields from old renderer constants. Exact existing JSON shape, projects empty. Escape plain text before ReportLab markup. At least 10pt body, target one page, never silently shrink under minimum. PDFs staged into out_dir; return layout failures without pretending accepted. Rendering is offline.

- [x] Test header values come from profile and old hardcoded contacts are absent; literal ampersands render; oversized resume reports overflow; both PDFs have selectable text.
- [x] Run intended failing tests then adapt the existing renderer/functions, keeping template structure where sensible.
- [x] Run tests and document layout/QA limitations; no paid calls.

## Task 3: Decisions, bounded generation, CLI (primary)

Files: policy/decisions.json, harness/pipeline.py, harness/cli.py, harness/__main__.py, tests/test_pipeline.py; examples/stibo.jd.md and other supplied attachment JDs.

Interfaces: pipeline creates draft structured JD data, validates it with Jev, evaluates requirement/evidence pairs, deterministically selects 8-10 block envelopes across four employers, calls writer per employer and summary/letter, checks/repairs each block independently, writes application JSON and calls Task 2 renderer. Store resume and letter blocks by stable IDs; preserve passing revisions. Save all source snapshots and use them on resume. Final global Jev audit checks clarity and coverage; unknown unsupported work remains honestly absent, rather than invented to force perfect coverage. No tool-based fit rejection.

- [x] Tests for stopped/failed gates never releasing accepted artifacts, fixed repair limits, resumed accepted blocks unchanged, and render-only not creating a provider.
- [x] Implement CLI new/resume/inspect/render with /done paste handling; readable errors and saved progress.
- [x] Add readable handoff and run report, manual-edit hash tracking, and documentation.

## Task 4: Run and review (primary plus independent review)

- [x] Run offline suite and independent code review; fix release/cache/boundary defects.
- [x] Once local key exists, inspect live model catalog and execute one Stibo run. Record actual decisions, repairs, token usage/cost and any uncertainty.
- [x] Inspect both PDF page images and extracted text; fix layout defects without altering approved claims silently.
- [x] If semantic checks fail, preserve draft and explain exact failure; no fake success. Compare readable output/trace with the existing approach; a single run cannot prove general superiority.
- [x] Update NOW.md/MEMORY.md with runnable commands, results and next input if blocked.

## Preflight and rulings

| Tasks | Shared interface | Ruling |
|---|---|---|
| 1 and 3 | provider/create/decide, canonical records, store | Primary owns both; keep typed public signatures stable |
| 2 and 3 | render_application(application, profile, out_dir) | Isolated renderer files; pipeline uses returned result and page checks |
| 1 | uncertain confidence calibration | Log distributions and mark first run experimental; no invented numeric confidence thresholds |
| 2 | missing profile email/link URLs | Omit missing optional fields; never copy unconfirmed renderer values |
| 3 | unresolved semantic judgment | Bounded repair then draft/review status, not silent acceptance |
| 4 | missing API key | Continue implementation/tests; real inference waits for local key |

Workspace ruling: this is a new non-Git workspace containing user source files, not an existing main branch. Preserve inputs, initialize a local prototype branch, do not push. No worktree needed to separate an existing code checkout. No full-system implementation or multi-provider framework is required for this slice.

Completion note: working first-run slice delivered on 20 September 2026; 24 offline tests pass. Stibo generated both PDFs with REVIEW_REQUIRED, described in FIRST-RUN.md. No controlled chat baseline or full calibration was run. The early Task 1 checkboxes remain unmarked where the combined wording includes verification not separately evidenced (such as a dedicated credential-redaction regression).

