# Harness v3 implementation plan

> For Sol: use superpowers:executing-plans inline after the user's model switch. No delegation or architecture changes are needed. Follow HARNESS-V3-DESIGN.md. User requested an Astra-to-Sol handoff; stop this design turn before implementing.

**Goal:** A substantial JD-tailored application using hierarchical evidence and item/group/document Jev decisions, without eight-bullet truncation or nested repair loops.

**Architecture:** YAML input, typed work/skill records, deterministic selection and renderer measurement, coherent writer call, explicit hierarchical checks, one bounded repair coordinator. Reuse the provider/cache/store rather than rebuilding them.

**Tech stack:** Python >=3.11, existing Pydantic/ReportLab/pypdf/OpenRouter adapters; add PyYAML safe loading with duplicate-key rejection.

**Spec:** HARNESS-V3-DESIGN.md. Its limits, taxonomy, status predicate and repetition policy are binding.

## Fixed decisions

- Max four bullets per employer; no eight-total rule, no forced four-per-employer minimum. Keep all employers and one independent project.
- One-page resume, readable fonts, no filler. Word ranges are writing guidance only, not retry triggers.
- Jev examines individual items and their parents. No whole-section PASS stands in for child checks.
- Writer produces prose/structured drafts; never scores, selects or validates.
- One initial draft plus at most two shared repair rounds, three writer attempts per ID. 80 HTTP attempts per job; no silent increases.
- New runs use writing_version=3. Old jobs/PDFs are immutable; inspect/offline render remain available.
- Retrofit is settled. No new tool-history approval or project-inventory request.
- Keep the public root schema; activate the existing `{name, period, bullets}` project shape. Internal records remain detailed until final export.
- Source and policy migration must be complete before a new paid run. Old snapshots remain usable.
- Do not claim ATS passing or writing superiority from local checks.

## Shared contracts

Define these in `harness/records.py` using StrictModel; schema validation is separate from semantic Jev questions. IDs are stable strings. Do not model graph objects or add databases.

```text
SourceRef: archive_sha256, start_line, end_line, quote
Fact: id, employer_id, system_id, kind, text, source_refs
Metric: id, employer_id, system_id, display_text, meaning, status, source_refs
Boundary: id, scope_ids, text, source_refs
Accomplishment: id, system_id, purpose, fact_ids, metric_ids, boundary_ids
SystemRecord: id, narrative, source_refs, problem_fact_ids, input_fact_ids,
  action_fact_ids, output_fact_ids, outcome_fact_ids, metric_ids,
  boundary_ids, status_fact_ids, accomplishments
EmployerRecord: id, company, titles, period, status_text, boundary_ids, systems
CanonicalV3: schema_version, source_archive, source_archive_sha256,
  profile, education, identity, administrative, policies,
  employers, facts, metrics, boundaries, prototype_pattern
Component: id, requirement_id, text, quote, priority
JobV3: company, role, location, thesis, requirements, components, stack_items
SkillItem: id, exact_term, jd_quote, kind, display_group, centrality,
  display_text, aliases
SkillGroup: id, label, item_ids
Candidate: id, employer_id, system_id, purpose, fact_ids, metric_ids,
  boundary_ids, component_support, primary_component_id, target_terms,
  relevance, specificity, contextual_only
Prototype: id, name, period, pattern_id, source_system_id,
  local_steps, outputs, target_terms, component_support, boundary_ids
Blueprint: job, skills, skill_groups, candidates, prototype,
  envelopes, fixed_fields, unselected_reasons
Envelope: id, kind, parent_id, role, purpose, source_fact_ids,
  source_metric_ids, boundary_ids, component_ids, target_terms, writing_guidance
DecisionNode: id, kind, parent_id, content_hash, dependency_hashes
DecisionCase: id, node_id, dimension, state, question, criteria, dependency_hash
Issue: code, node_ids, target_ids, instruction, decision_ids, unresolved
AssessmentV3: leaves, parents, component_coverage, relationships,
  issues, unresolved, text_hashes, selected_ids, passed
LayoutSelection: selected_ids, omitted, predicted_height_pt,
  available_height_pt, overflow_pt, checks
```

Use enum fields from the design for semantic kinds/status. Dictionaries are appropriate for provider choice distributions and content-addressed lookup maps. Source/metric references must resolve to the candidate's system except explicit global/employer boundary inheritance. Unknown project date is an empty string. Prototype pattern has statement, local_scope, publication_status, source_session_note, restrictions; do not invent repository URL.

## Task 1: Complete source migration and canonical policy update

Files: create `canonical.yaml`, `archive/canonical-v2.md`, `migration-report.json`, `harness/records.py`, `harness/canonical.py`, `scripts/check_canonical.py`, `tests/test_canonical_v3.py`; edit `01-CANONICAL.md`, `00-APPLICATION-ENGINE.md`, `pyproject.toml`. Leave `harness/sources.py` available for old snapshots.

Interfaces:

```python
load_canonical_v3(path: Path) -> CanonicalV3
check_migration(canonical: CanonicalV3, archive_path: Path) -> dict
```

- [ ] Write tests first: duplicate YAML keys fail; metric references crossing systems fail; achieved vs target status survives; each source quote matches exact archive lines; every source block has a mapped destination/disposition.
- [ ] Run `python -m unittest discover -s tests -p test_canonical_v3.py -v`, observe the missing implementation failures.
- [ ] Archive original bytes; record original hash AA55979958BE8F1DC9C247281677658CCE491CBC7FABD292BB84150039909460. Build populated YAML from the full canonical, preserving all four employers, both education entries, identity, administrative facts and constraints. Ensure cost-reduction, approval-latency, Cognizant scale and latency, Think Round review status, and Formula Dream implementation facets are separate usable facts linked to systems.
- [ ] Implement safe load + strict models + reference validation. `check_migration` iterates original nonblank source blocks, verifies quotes and mappings and returns missing/invalid reference lists; it does not merely compare counts.
- [ ] Record the user's prototype authorization and remove contradictory active instructions in engine/Markdown. Make Markdown point clearly to YAML. No runtime input reads both as competing authorities.
- [ ] Run tests and `python -m scripts.check_canonical`; inspect the migration report for semantic completeness, especially details stored outside old capability headings. Tests cannot alone prove quality of extraction.
- [ ] Commit this isolated migration after reviewing the factual changes. Do not commit `.env` or paid jobs.

Concrete regression:

```python
def test_company_metric_cannot_be_claimed_by_local_project(self):
    c = make_canonical_v3_fixture()
    c.prototype_pattern['metric_ids'] = ['corominas.client-volume']
    with self.assertRaises(ValueError):
        validate_canonical_fixture(c)
```

`make_canonical_v3_fixture` and `validate_canonical_fixture` belong in `tests/v3_support.py`; the latter runs the same public model and reference validation used by `load_canonical_v3`, not separate test logic. Include two employers/systems in minimal fixtures, and the real four-employer source in migration tests.

## Task 2: JD components and hierarchical skills

Files: create `harness/skills.py`, `tests/test_skills_v3.py`; edit `harness/models.py`, `harness/pipeline.py`, `policy/decisions.json`; extend records and v3 fixtures from Task 1.

Interfaces:

```python
analyze_job_v3(store, provider, policy, jd: str) -> JobV3
classify_skills(provider, policy, job: JobV3) -> tuple[list[SkillItem], list[SkillGroup], list[Issue]]
skill_cases(job, items, groups, decisions) -> list[DecisionCase]
```

- [ ] Tests: atomize a composite production-AI requirement into deployment, integration and operational-control components without losing source quotations; absence of a component cannot disappear from coverage. No extraction target of 6-12 requirements.
- [ ] Type tests use fixed Jev answer doubles: OpenAI PROVIDER, LangChain FRAMEWORK_LIBRARY, Python LANGUAGE, Docker DEPLOYMENT_TOOL, CI/CD and MLOps METHOD_ARCHITECTURE, AI DOMAIN, LLMs UNSPECIFIED_FAMILY. Assert group labels are chosen from the permitted taxonomy.
- [ ] Test that every non-domain JD stack term survives with exact spelling/alias; an unspecified model/database family adds no vendor. Domain items remain in the report rather than masquerading as technologies.
- [ ] Test that a category PASS plus a child FAIL produces unresolved/failed Skills. Membership answers must name every child, not a single group Boolean.
- [ ] Implement component extraction as a writer-created draft plus existing bounded Jev interpretation check. Replace old flat `JobDraft` v3 consumption while keeping old offline paths.
- [ ] Implement Jev kind/relevance/group decisions with fixed options; assemble display groups in code. Store decisions before creating prose. UNCERTAIN remains unresolved; no identical-question retry to manufacture certainty.
- [ ] Run module tests and save a readable offline example of the McKesson skill group assembly from controlled decisions. It is a layout/example fixture, not a live Jev judgment.
- [ ] Commit.

## Task 3: Candidate planning, project and complete writer brief

Files: create `harness/planning_v3.py`, `harness/writing_v3.py`, `tests/test_planning_v3.py`; edit `harness/models.py` and relevant policy; reuse source enums and provider.

Interfaces:

```python
build_blueprint(canonical, job, skills, groups, decisions: dict) -> Blueprint
planning_cases(canonical, job) -> list[DecisionCase]
writer_payload(blueprint: Blueprint, texts: dict, writable_ids: list[str], issues: list[Issue]) -> dict
```

- [ ] Write tests: a fixture with twelve distinct relevant accomplishments across four employers yields twelve candidates when each has <=4; an employer with six eligible candidates yields <=4; a relevant older employer may get four; eight is never a stopping condition.
- [ ] Test distinct accomplishments in one system can both be selected; two aliases of the same achievement cannot consume two slots. Only compatible same-system facts/metrics can compose a candidate.
- [ ] Test project uses local workflow and target tools, no employer portfolio metric, no invented period or URL, and existing `{name, period, bullets}` shape. Remove `max_length=0` and renderer's blanket empty-project rejection; keep legacy `[]` valid.
- [ ] Implement planning cases for component coverage, candidate relevance, concrete output and distinct purpose. Code orders candidates with the design's lexicographic rule; no new weighted confidence threshold or recency term.
- [ ] Build a blueprint with approved skill groups, all four employer entries, 1-4 candidates each, one local project, 2-3 summary sentences and three letter paragraphs. Every ID has an explicit parent/purpose/source set.
- [ ] Produce one full writer request with all candidates and outline visible. Remove per-employer initial calls for v3. Word guidance is metadata/instructions only; do not create `SUMMARY_TOO_SHORT`, `PAGE_TOO_EMPTY` or fixed bullet-word rejection rules.
- [ ] Tests assert writer returns exactly supplied IDs; no skills/chronology selection is delegated to it. Check truncated/malformed output is not accepted and consumes the same attempt budget.
- [ ] Run focused tests, inspect payload fixture, commit.

Concrete regression:

```python
def test_twelve_distinct_candidates_are_not_cut_to_eight(self):
    c, job, decisions = make_twelve_candidate_case()
    blueprint = build_blueprint(c, job, [], [], decisions)
    self.assertEqual(len(blueprint.candidates), 12)
    counts = Counter(b.employer_id for b in blueprint.candidates)
    self.assertTrue(all(1 <= n <= 4 for n in counts.values()))
```

Create `make_twelve_candidate_case` in v3_support with three independently relevant accomplishments per employer and fixed known Direct/DISTINCT decisions. Do not use provider calls in tests.

## Task 4: Hierarchical assessment and targeted dependencies

Files: create `harness/assessment_v3.py`, `tests/test_hierarchy_v3.py`; edit `policy/decisions.json`; reuse `assessment._decision_cases` transport/cache after extracting a shared adapter if needed.

Interfaces:

```python
leaf_cases(blueprint: Blueprint, texts: dict[str, str]) -> list[DecisionCase]
parent_cases(blueprint, texts, selected_ids, leaf_decisions) -> list[DecisionCase]
assess_v3(provider, policy, blueprint, texts, selected_ids) -> AssessmentV3
required_checks_pass(report: AssessmentV3) -> bool
invalidated_case_ids(cases, changed_node_ids: set[str]) -> set[str]
```

- [ ] Test required skills item FAIL cannot be erased by Skills PASS; bullet FAIL cannot be erased by employer/Experience PASS; required UNCERTAIN remains unresolved.
- [ ] Test parent context includes its actual children and child decisions. Individual bullet state includes source actions, output, metric scope and restrictions, not an entire unrelated canonical.
- [ ] Test permitted repeats (tool Skills/Experience, capability Summary/Experience, resume story in letter, distinct same-system results); rejected repeats (same letter case in opening and middle; same accomplishment twice within Experience).
- [ ] Test a missing CORE component with no candidate remains in report as Missing and blocks acceptance; PARTIAL is displayed and not promoted to full coverage. Supporting/peripheral omissions are visible informational rows.
- [ ] Implement the explicit levels in the design table. Each answer records node, dimension, dependencies and options. Use separate narrow questions batched into shared requests; no generic recursive evaluator engine.
- [ ] Parent issues use per-member/group-fit or pair answers to identify writable IDs. Unlocalized parent FAIL remains unresolved rather than rewriting the whole section speculatively. Employer MATERIAL_VALUE check uses omitted candidate IDs and current selected employer hashes; reallocation is bounded once per revision.
- [ ] Test changing one bullet invalidates itself, employer, related component/pair/ancestor checks, but leaves another employer's bullets and unchanged skill cases cached.
- [ ] Test the single-case >75k guard and existing shared-state deduplication. Separate logical question counts from HTTP request counts.
- [ ] Run focused tests and commit.

Concrete status test:

```python
def test_global_pass_never_overrides_missing_core_component(self):
    report = make_passing_assessment_v3()
    report.component_coverage['core-deployment'] = {
        'priority': 'CORE', 'status': 'Missing', 'expressed_ids': []}
    self.assertFalse(required_checks_pass(report))
```

`make_passing_assessment_v3` supplies required leaves and parents plus text hashes in v3_support. Mutate one actual field at a time to test release invariants.

## Task 5: Shared renderer measurement and useful content fitting

Files: create `harness/layout_v3.py`, `tests/test_layout_v3.py`; edit `renderer/build.py`, `harness/rendering.py`, `tests/test_rendering.py`.

Interfaces:

```python
resume_flowables(application_resume: dict, profile: dict) -> list
measure_resume(application_resume: dict, profile: dict) -> dict
select_fitting_experience(blueprint, texts, leaf_report, profile) -> LayoutSelection
```

- [ ] Extract a shared story builder used by measurement and PDF build; include every spacer, KeepTogether/table width, heading and paragraph style. Use ReportLab's layout behavior rather than estimating characters/line.
- [ ] Add typed Project validation with nonempty name, empty-or-real period and two bullets for v3 output; the legacy renderer still permits empty projects. Keep root keys and existing item shape.
- [ ] Test >8 useful short bullets fit when space permits. Test all four employers and one project survive fit selection. Test useful older work can displace less relevant newer work. Test selected subsets maximize actual component coverage before cosmetic fullness.
- [ ] Implement feasible subset enumeration with <=4 per employer and >=1 each, fixed other sections, stable ordering. At most 65,536 subsets of sixteen candidates; cache measured block heights and avoid writing PDFs for every subset. Measure complete candidate finalists with shared layout logic; final PDF page count confirms the result.
- [ ] Test mandatory content overflow yields measured PAGE_OVERFLOW and never 8-point text, missing project, or omitted employer. No occupancy percentage gate or arbitrary empty-space writer retry.
- [ ] Build a clearly labeled offline layout fixture with summary, grouped skills, twelve concise bullets, project and education. Render once, inspect page image and compare measured vs actual page count. This fixture tests structure, not generated writing quality.
- [ ] Run focused tests, commit.

If additive block heights do not match final flowable pagination, fix shared measurement. Do not accept a layout approximation that passes only short test paragraphs.

## Task 6: Single coordinator, status, reporting and snapshot compatibility

Files: edit `harness/generation.py`, `harness/pipeline.py`, `harness/store.py`, `harness/cli.py`, `harness/comparison.py`, `config.json`; create `harness/reporting.py`, `tests/test_run_v3.py`, `tests/test_reporting_v3.py`; update README/NOW/MEMORY.

Interfaces:

```python
run_writing_v3(store, provider, policy, blueprint, profile) -> dict
export_application_v3(blueprint, texts, selected_ids, application_date) -> dict
write_coverage_report(folder, blueprint, report, layout, usage) -> None
```

- [ ] Regression tests first: crash before writer response, after pending response, after leaf checks, after selecting repair targets, and after repair response but before parent assessment. Reopen RunStore and prove no lost draft, duplicated completed writer call or reset budget. Test at least one A/B/A repeated failure ends within three versions.
- [ ] Persist revision/phase/selected IDs/target IDs/issues/attempt reservations/stage baseline before network calls. Resume pending phase rather than reassessing the old draft and scheduling a duplicate repair. Planning uses `begin_stage`; keep elapsed naming accurate across pauses.
- [ ] Integrate one initial writer call, leaves, fit selection, parents and all-component coverage. One shared repair coordinator collects actionable IDs from every level. Skills moves/deduplication are deterministic; only prose is sent for rewrite. Invalidate dependent cases, not whole unrelated sections.
- [ ] Replace v3 release computation with `required_checks_pass(report) AND structural_checks AND final_pdf_checks`. Do not reuse globals-only release_status. Preserve REVIEW_REQUIRED on planning gaps, partial core evidence, unresolved parents or budget exhaustion.
- [ ] Test offline rendering old jobs without providers/credentials. Test v3 refuses old resume BEFORE state mutation; projects [] still render for historical jobs. New snapshots contain canonical.yaml, engine, config, policy, JD and code versions.
- [ ] Update comparison runner to support version-specific snapshots and equivalent v3 fixed structure. It remains one creation call, never mutates the harness run, reports schema/layout validity separately from semantic quality. Do not automatically pay for another comparison this task.
- [ ] Create coverage.md/JSON with every component including uncovered ones; skill kind/group/occurrences; employer count and omission reason; project scope; concrete outstanding issues; actual calls/cost/questions/time. Terminal output links to that report with plain counts and failures.
- [ ] Run all tests and source migration check, check Git diff, update docs with actual implementation limits. Commit.

Representative failure-resume invariant:

```python
def test_saved_response_is_consumed_without_another_writer_call(self):
    store, provider, blueprint, profile = interrupted_v3_case('after_pending_response')
    resumed = RunStore(store.folder)
    provider.create = Mock(side_effect=AssertionError('response already saved'))
    run_writing_v3(resumed, provider, passing_policy_fixture(), blueprint, profile)
    self.assertEqual(resumed.state['blocks']['summary.1']['attempt_count'], 1)
```

Implement `interrupted_v3_case` in v3_support using an injected crash hook in the coordinator and fake provider that supplies passing semantic results; no real network. Also test repair responses this way; an initial-only resume test is insufficient.

## Task 7: Show structure, then the bounded live experiment

- [ ] Before paid calls, present a concise checkpoint: migration coverage complete/incomplete; offline test result; sample Skills hierarchy; planned employer candidate counts; included project; one-page fixture image. State clearly these are fixture/structure checks, not generated quality claims. Do not ask for new facts already provided or a blanket tool inventory.
- [ ] When executing the user-authorized experiment, start fresh v3 job folders for Stibo and McKesson. Run once per case; normal bounded repairs are included. Do not keep tuning and rerunning until Jev produces PASS.
- [ ] Inspect both PDFs for each case, read the coverage report against the actual JD, check useful page content and classified skills. Report missing/partial components explicitly. Keep REVIEW_REQUIRED when applicable.
- [ ] Compare to preserved v2 and one-shot outputs as historical evidence, noting changed brief/structure makes this a product improvement check, not a controlled writer-only A/B experiment.
- [ ] Deliver PDFs plus short visible coverage table and actual cost. Do not make the user decode raw traces or accept a blind-choice exercise before seeing whether their requirements were met.
- [ ] Update NOW/MEMORY with actual paths, statuses, test count, costs and remaining issues. Stop for user output review. No further architecture decisions delegated silently to Sol.

## Command reference and handoff review

Bundled Python on this machine:

```powershell
$taskPython = 'C:\Users\91910\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $taskPython -m unittest discover -s tests -v
& $taskPython -m scripts.check_canonical
& $taskPython -m harness new --jd examples\stibo.jd.md
& $taskPython -m harness new --jd examples\mckesson.jd.md
```

Network calls use the normal sandbox approval route; prior user authorization covers these JDs/evidence being sent to the configured writer/Jev providers. Never print `.env`. Git changes require the normal .git approval path here; no push/merge. Current commits: 60f8960 implementation, 8228574 corrected requirements.

Self-review mapping: YAML/project-policy migration -> Task 1; JD depth/skills -> Task 2; no eight cap/substantive draft/project -> Task 3; per-item/parent Jev -> Task 4; one-page useful selection -> Task 5; bounded repairs/full status/visible report/compatibility -> Task 6; real output and communication -> Task 7.

Do not invent thresholds, add retry loops, silently simplify YAML to section strings, or reinstate fixed global bullet counts to make tests easy. If a specified combination cannot be implemented coherently, explain the exact conflict and stop for the user rather than shipping a narrowed interpretation.
