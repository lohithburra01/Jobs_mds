# Writing v2 implementation plan

> For agentic workers: execute inline using superpowers:executing-plans after the user switches to Sol. Do not start implementation during the Astra design turn. User's model/cost instructions override default agent delegation.

**Goal:** Produce specific, readable applications and repair identified writing problems without rewriting passing blocks or looping indefinitely.

**Architecture:** Fixed writing roles, complete-document diagnosis, deterministic repair selection and one persistent three-attempt block budget. Jev classifies; the writer creates; code controls state.

**Tech stack:** Existing Python/Pydantic/OpenRouter/ReportLab stack; unittest; no new service or dependency.

**Spec:** WRITING-V2-DESIGN.md. Read it before implementing. Retain the existing 24 offline tests and v1 artifacts.

## Constraints

- Preserve public Application schema, canonical facts and settled functional stack retrofit.
- Initial draft plus two repairs per block; max 80 HTTP attempts per harness job.
- One experiment per JD on this revision; never rewrite v1 output in place.
- No generative validators. No arbitrary probability threshold.
- Do not print .env, embed credentials in records or commit jobs.
- Stop for a model-switch discussion only when a material structural decision falls outside this spec; routine fixes belong to Sol.

## Task 1: Writing plan and limits

Files: harness/planning.py, harness/pipeline.py (build_plan), policy/decisions.json, config.json; new harness/writing_plan.py and tests/test_writing_plan.py.

Interface: build_writing_plan(canonical: dict, job: dict, plan: dict) -> list[dict]. Return stable block IDs and existing envelope fields plus primary_requirement_id, potential_requirement_ids, role, target_words and max_words. The proof paragraph has exactly one selected source. Caller persists the result once per new job.

- [ ] Add synthetic tests for seven requirements sharing one source: no bullet purpose contains seven concatenated requirements; unassigned requirements remain coverage potential. Every employer remains, every bullet has one purpose.
- [ ] Add tie-break tests where equal relevance selects a concrete outcome over a general capability, but higher relevance still outranks an irrelevant metric.
- [ ] Add letter tests: three distinct roles, one reserved proof source, opening/closing cannot retell it. Assert bullet hard limit38, summary60 and paragraph maxima60/95/60.
- [ ] Run the new test module and observe failures; implement the deterministic assignment and evidence-specificity Jev question described in the spec, then rerun it.

Test assertions to include:

```python
self.assertEqual(len({b['id'] for b in envelopes}), len(envelopes))
self.assertEqual(len(by_id['letter_2']['evidence']), 1)
self.assertEqual(by_id['letter_1']['role'], 'opening')
self.assertEqual(by_id['letter_3']['role'], 'closing')
self.assertTrue(all(b['max_words'] == 38 for b in envelopes if b['kind'] == 'bullet'))
```

## Task 2: Specific issues and repair targeting

Files: new harness/assessment.py, policy/decisions.json; new tests/test_assessment.py and tests/fixtures/writing_cases.json.

Interface: assess(provider, policy: dict, envelopes: list[dict], texts: dict[str,str], job: dict) -> dict with block_issues, relationship_issues, requirement_coverage, global_verdicts and text_hashes. Each issue stores code, affected_ids, target_id (or null), instruction, observed hashes and full Jev response. Return uncertainty as unresolved, not a fabricated repair.

Interface: repair_targets(report: dict, records: dict) -> list[str]. Return only deterministic targets with actionable issues and remaining attempts. No target is inferred solely from a global FAIL.

- [ ] Write tests using fixed Jev response doubles: redundant opening/proof selects opening; same resume/letter example is allowed; summary/bullet repetition selects summary; unrelated passing blocks are absent from repair targets.
- [ ] Add tests for a named missing requirement, unlocalized global FAIL, contradictory pair with no uniquely failed grounding check, and UNCERTAIN: only the first case has a writable target, if an owner exists.
- [ ] Add length tests:35 words alone is not a failure; a separate UNNECESSARY decision causes TRIM_DETAIL;39 words produces count/excess/target feedback.
- [ ] Implement batched local, relationship, requirement and final checks. Reuse existing choice/batched_decide and provider cache. Relationship question state contains only the needed pair/roles/policy so unrelated edits do not invalidate it.
- [ ] Add the eight editorial fixture types specified in the design, marked as authored expectations. Do not make network inference part of unittest or label these examples calibrated accuracy.

## Task 3: Bounded complete-document repair

Files: harness/generation.py, harness/pipeline.py, harness/store.py only if required for atomic state; tests/test_pipeline.py and new tests/test_repair_rounds.py.

Interfaces: Generation.draft(envelopes, context, writable_ids, visible_texts, issues) creates/checkpoints one batch without performing a hidden repair loop. A new run_writing(store, provider, policy, envelopes, context, job) -> dict[str,str] owns rounds and calls assess/repair_targets. Existing generation behavior may be retired for new runs; keep its tested invariants, adapting tests to the new API where necessary.

Coordinator algorithm:

```text
Create/checkpoint initial drafts for missing blocks, in employer/summary/letter batches.
For current draft revision:
    resume pending classification before scheduling another writer call
    assess current draft; checkpoint report with text hashes
    if all checks pass: finish
    select diagnosed targets with attempt_count < 3
    if no targets or two repair rounds already completed: finish as review
    persist target batch/round cursor and issue set
    draft targets with whole draft visible and only those IDs writable
    keep passing text unchanged; advance cursor only after pending work completes
Render current draft and determine status from current checks.
```

- [ ] Write a failing regression where all blocks pass locally but opening/proof duplicate globally; one opening repair must occur, with the proof visible and unchanged.
- [ ] Write interruption tests before writer response, after pending draft save, after assessment save and midway through repair batches. Reopening a RunStore must neither reset attempt counts nor lose completed drafts.
- [ ] Add fixtures for identical failing text and A/B/A cycling with the same issue set. Assert bounded termination and preserved revisions.
- [ ] Add a test that no block exceeds three attempts across local and relationship issues, and no text can inherit a PASS keyed to an earlier hash.
- [ ] Implement the coordinator and payload separation. Reuse persistent pending_draft recovery already present; do not reset attempts merely because neighbors changed.
- [ ] Refactor pipeline.execute to use the new writing coordinator, removing its old employer-local repair loops and after-the-fact-only global check. Continue assembling fixed chronology/education and rendering even a review draft.
- [ ] Add writing_version=2. In CLI/pipeline resume, refuse v1 mismatch before invalidating releases or changing run.json. Keep inspect/render offline and working. Test both paths.

## Task 4: One-shot comparison and real outputs

Files: new scripts/compare_writing.py, tests/test_comparison.py; README.md and FIRST-RUN.md supplement/new comparison report. Keep paid comparison artifacts in ignored jobs/ folders.

Interface: script accepts --job (completed v2 folder). It loads its exact saved writing plan, sources, JD, date and config; makes one writer creation call returning Application JSON; renders it with the same profile/template. It saves to a separate comparison directory. It never mutates harness run state or changes harness acceptance. Failure records and usage are preserved; no repair or hidden second attempt.

- [ ] Test with fake provider that only one creation call is made, original job files remain byte-identical, invalid output is recorded, and the same profile/date/renderer are used.
- [ ] Include full source boundaries in the baseline prompt but no harness-generated prose, diagnostics or repairs. This isolates the writing orchestration benefit given equal prepared context.
- [ ] Record writer/classifier request counts and provider-reported costs by stage. Record elapsed times for new calls; do not invent elapsed time for the historical v1 run. Baseline incremental cost and shared preparation cost must be distinguishable.
- [ ] Run the complete offline suite once after implementation. Fix meaningful failures before paying for calls. Ensure original source hashes and first-run files are unchanged.
- [ ] Run a fresh v2 Stibo job, preserve its status, rasterize and inspect both PDFs. Make its one-shot comparison. Repeat once with examples/mckesson.jd.md. If transport or schema failure blocks a case, report it; do not present fabricated comparison output.
- [ ] Produce A/B output folders with recorded randomized mapping separate from viewing text. Ask the user to choose which they would send using the five plain-language criteria in the spec, allowing neither/tie. Do not claim harness superiority from Jev pass rates alone.
- [ ] Update README/NOW/MEMORY with actual commands, statuses, costs and remaining writing problems. Stop here for output review rather than starting another tuning loop automatically.

## Existing operational issue

Local Git has no first commit. An earlier git add escalation failed because automatic approval review hit its usage limit; files are saved but untracked. Sol may retry through the normal approval path once available. Do not bypass the sandbox or let Git housekeeping block inspecting the generated applications.
