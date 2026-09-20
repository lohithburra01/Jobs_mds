# Harness v3: structured inputs and detailed Jev decisions

Status: Astra design handoff, 20 September 2026. This turn changes documentation only. Implement after the user's switch to Sol. Supersedes v1/v2 design wherever conflicting. The user explicitly requested this plan; no additional planning questionnaire is needed.

## 1. Outcome and constraints

Paste JD -> readable, substantial, one-page resume + cover letter + a short JD coverage report. The candidate should not have to audit model traces to discover missing content. Runtime remains a local CLI using OpenRouter. Jev makes semantic selections/checks; the writer creates prose and structured drafts only; code handles exact constraints, assembly and execution.

Binding corrections:

- Maximum four experience bullets per employer. Remove the eight-bullet total target/cap. Four employers imply at most sixteen, not a requirement to use sixteen.
- Preserve every employer; relevance and distinct useful work determine space, not recency or equal quotas.
- One page, concise prose and no unnecessary repetition still apply. Do not shrink fonts, pad spacing, add filler or relax factual boundaries to fill the page.
- Build useful content before checking it. Do not add a summary-length evaluator, page-fullness evaluator, new retry tiers or a recursive evaluator framework.
- Jev must examine each skill, each category and Skills overall; each bullet, each employer and Experience overall; then the assembled application. A parent PASS never replaces child decisions.
- A normal v3 application includes one JD-relevant independent project, using the user's confirmed local-prototype/GitHub working pattern and authorized functional retrofit. No request for a complete tool/project inventory.
- Use structured YAML evidence with employer/system/action/outcome relationships. YAML is an input organization change, not a claim that serialization itself improves intelligence.
- Preserve settled stack retrofit. No employer-tool-history questions or fit rejection from absent tool names.
- Preserve employers, dates, role status, metric scope and project-vs-employer scale. Unknown project URL/date/metrics stay empty or omitted, never borrowed from employer results.

The eight-bullet limit was a design decision explicitly retained in the previous Astra v2 handoff. It is not attributable only to Sol's implementation. This design removes it at the source rather than asking Sol to improvise.

## 2. Architecture choice

Chosen: typed YAML evidence + explicit hierarchy + batched Jev decisions + coherent full-draft writing + renderer-based content selection + the existing bounded repair coordinator.

Rejected: merely raising limits (would leave flat skills, whole-section evidence and missing projects); adding more independent evaluators/retry loops (would multiply calls without improving the brief).

Sequence:

1. Load and snapshot the structured canonical, JD, policies and configuration.
2. Writer extracts JD requirements, their work components and literal stack terms. Jev checks each component plus extraction completeness against the original JD.
3. Jev classifies each skill term and each work component. Code assembles categories and up to four useful bullet candidates per employer; prepares one project.
4. Writer creates all selected bullet candidates, a summary and the three letter paragraphs together with the full blueprint visible. Skill labels/items and chronology are assembled by code.
5. Jev evaluates each candidate bullet, summary sentence, project bullet and letter paragraph. Code measures actual rendered heights and selects the strongest fitting experience subset while reserving the other required sections.
6. Jev checks the selected employer entries, categories, sections, exact requirement coverage and document relationships. Passing children remain passing but cannot override a parent issue.
7. A single coordinator collects all actionable issues and rewrites only implicated prose IDs; at most two repair rounds total. Rerun only affected judgments and necessary parent/coverage checks.
8. Export application JSON, PDFs and coverage.md. Final acceptance uses all required current decisions, structural results and layout results, not only three global verdicts.

Granularity refers to separate questions/answers and separately tracked objects. It does not mean one HTTP call per question. Keep existing deduplicated Jev batching and per-case caching. A whole section can be context for several narrow questions, but never the sole PASS for all its members.

## 3. Canonical YAML

`canonical.yaml` becomes the single editable evidence source for v3. YAML loading uses a SafeLoader that rejects duplicate keys; quoted date strings and strict Pydantic validation. PyYAML is the only proposed new dependency. No runtime free-text canonical extraction.

Migration:

- Preserve the original Markdown bytes in `archive/canonical-v2.md` and its SHA256 in the YAML metadata.
- Create YAML once from ALL canonical content, not only headings recognized by the old `other_units` list. Read each employer in full during migration.
- Retain exact source excerpts plus source references alongside structured facts. Every original block of content must be mapped in migration-report.json to a field or archived/superseded instruction with a stated reason. Important facts must be structured and usable, not merely buried in an archive field.
- Keep profile, education, full identity, administrative routing, chronology, system status, outcome/metric scopes and global/employer/system restrictions. Record the new project authorization as a current-session user correction.
- Replace the active `01-CANONICAL.md` with an explicit pointer to YAML and archive; keep engine prose as instructions, not a second factual store. Update contradictory project and density instructions in `00-APPLICATION-ENGINE.md` in the same implementation task.
- Historical jobs continue using their existing immutable Markdown snapshots for offline inspect/render. Version-3 generation/resume uses YAML snapshots only. No silent migration of paid v1/v2 jobs.

Internal hierarchy:

```yaml
schema_version: 3
source_archive: archive/canonical-v2.md
profile: {}                       # confirmed personal fields and optional links
education: []
identity: {}                      # professional spine, breadth, maintainability
administrative: {}                # retained facts/routing, not resume prose
policies:
  stack_retrofit: functional
  max_bullets_per_employer: 4
  include_independent_project: true
employers:
  - id: corominas-consulting
    company: Corominas Consulting
    titles: ['Manager, AI & Automation']
    period: 'Jun 2026 - Sep 2026'
    status_text: 'System-level rollout status retained per source.'
    boundary_ids: []
    systems:
      - id: corominas.client-pipeline
        source_refs: []
        narrative: 'Exact source excerpt retained during migration.'
        problem_fact_ids: []
        input_fact_ids: []
        action_fact_ids: []
        output_fact_ids: []
        outcome_fact_ids: []
        metric_ids: []
        boundary_ids: []
        status_fact_ids: []
        accomplishments: []       # distinct groupings of compatible fact IDs
facts: []
metrics: []
boundaries: []
prototype_pattern: {}
```

This is a schema illustration, not a completed migrated canonical. Sol must populate it from the source. Each fact has `id, employer_id, system_id, kind, text, source_refs`; kind is problem/input/action/output/outcome/status. Each metric has `id, employer_id, system_id, display_text, meaning, status, source_refs`; status is achieved/target/derived. Each boundary has `id, scope_ids, text, source_refs`. Each source ref has archive hash, line range and exact quote; validate quotes against the archived file. A fact belongs to one system; shared facts use explicit references, never copies implying a second achievement.

A bullet candidate groups compatible fact IDs from ONE system into one useful accomplishment: action + output/consequence + optional same-system metric. It must not be one bullet per raw fact. Multiple bullets may come from one system only for distinct accomplishments. Jev makes DISTINCT/REDUNDANT decisions between candidate purposes before writing. No employer outcome or launch status may migrate across systems through aggregation.

Each migrated accomplishment has `id, system_id, purpose, fact_ids, metric_ids, boundary_ids`. Purpose describes a work angle, not a frozen resume bullet. The migration creates these from the full systems; runtime Jev selects among them and the writer reconstructs prose. Migration report checks no useful action/outcome disappeared because only one accomplishment was kept per system. No per-JD generative selector is introduced.

Prototype pattern records the user's statement that small local versions precede larger implementations and are published on GitHub. Select a workflow from these same kinds of work, describe local inputs/steps/output with the JD stack, and use a descriptive project title. Do not represent the company system, its clients, its volume or its savings as project results. GitHub publication is authorized; a particular repository URL/name/date is not supplied. This pattern is sufficient input; no runtime demand for an exhaustive inventory.

## 4. Job structure and skills

Job structure: `requirements[]` with IDs, literal source quotations, priority and `components[]`. Each component is a concrete action, input, integration, control or output the JD asks for. Broad requirements do not swallow critical components. No added target of 6-12 requirements; extraction schema/request-size limits are transport safeguards and must never silently drop a component. Each component receives a Jev priority/relevance judgment; all remain visible in coverage.md.

Stack items: `id, exact_term, jd_quote, kind, display_group, centrality, display_text, aliases[]`. Preserve JD literals in the displayed item or its alias. Exact products are not inferred from broad domains.

Jev classifies each item with these fixed kind options:

| Kind | Examples | Display group |
|---|---|---|
| LANGUAGE | Python, SQL, TypeScript | Languages & interfaces |
| INTERFACE | REST APIs, APIs | Languages & interfaces |
| FRAMEWORK_LIBRARY | LangChain, LangGraph, FastAPI | AI frameworks & providers, or Software frameworks |
| MODEL | A specifically named model/family | AI models & providers |
| PROVIDER | OpenAI | AI frameworks & providers, or AI models & providers |
| CLOUD_PLATFORM_SERVICE | AWS, Azure, Lambda | Cloud & data platforms |
| DATABASE_STORAGE | PostgreSQL, a named vector database | Cloud & data platforms |
| AUTOMATION_ORCHESTRATION | UiPath, n8n | Automation & orchestration |
| DEPLOYMENT_TOOL | Docker, Kubernetes | Deployment & operations |
| DEVELOPMENT_TOOL | Git, test/CI tooling | Development tools |
| METHOD_ARCHITECTURE | RAG, prompt engineering, CI/CD, MLOps | Methods & practices |
| DOMAIN | AI, automation | Use in role/experience context; not a tool list |
| UNSPECIFIED_FAMILY | LLMs, vector databases | Methods & practices with a concrete capability phrase |
| UNCERTAIN | Cannot classify from context | unresolved item; never silently accepted |

Policy holds all display group options and their allowed kinds. Jev chooses the best allowed group for each item using JD context; it may not invent category labels. Merge AI model/provider/framework groups under `AI frameworks, models & providers` when both would otherwise be small. Preserve accurate type internally after merging. Display only nonempty groups; prefer roughly 3-6 lines, not a forced line or category count. More are permitted when the JD actually needs them.

Examples of correct specificity:

- `LLMs` can become `LLM integration (LLMs)` when the JD asks to integrate them; it must not become a claim to know every model or an arbitrarily chosen model family.
- `vector databases` can remain `vector databases` within a retrieval capability phrase; do not invent Pinecone or another vendor for a JD that named none.
- `RAG` and `prompt engineering` are valid methods/skills. They are not products, and do not need to be removed merely because they are broad.
- `CI/CD` and `MLOps` are valid practices; do not add an unrequested product to make them appear more concrete.
- Bare `AI`/`automation` domain terms remain represented in summary/experience; exact implementation technologies belong in Skills. Report their domain classification so removal from the tool list is visible.

A skill group can include a broad area and concrete subskills ONLY when the hierarchy is explicit: e.g. `Deployment & operations: Docker, Kubernetes; practices: CI/CD, MLOps`. No implication that a practice is a product. Do not create extra subtables or a knowledge-graph UI in the resume.

Skills are assembled from approved item records; the writer cannot add arbitrary vendors or rearrange categories. Detailed checks:

1. Item: right type, correct exact name, relevant to JD, suitable specificity, correct assigned group. Each dimension has its own fixed-choice answer when semantic; exact spelling is code.
2. Group: label accurately describes members, members form a coherent category, no repeated item/alias. Per-member group-fit answers identify the item to move. Group checks cannot blanket-pass unexamined children.
3. Whole Skills: completeness against classified JD implementation terms, ordering by centrality, unnecessary duplication, no irrelevant source-side vendors. Exact coverage/alias deduplication is code; semantic duplicate pairs use Jev.

Incorrect classification is an explicit unresolved planning decision; it does not launch a prose rewrite loop. Repeating Jev on identical inputs cannot count as resolution. Writer-created display phrases can be corrected in the common prose repair round, preserving the literal term and its approved group.

## 5. Experience selection and first-draft brief

Evaluate every relevant system/action/consequence grouping against each JD work component. Use existing Direct/Partial/Adjacent/No Support/Uncertain distinctions; tool history is excluded. Jev also answers whether a candidate adds a DISTINCT useful point and whether its work is central/supporting/incidental for this JD.

Select up to four useful candidates per employer using stable lexicographic ordering: new direct core-component coverage, additional substantive core evidence, new supporting coverage, concrete useful work/outcome, source ID. Candidate-level uncertainty is retained explicitly. All employers remain; where none is relevant, retain its strongest real transferable work, mark that choice as contextual in coverage, and do not call it direct JD proof. Never guarantee Corominas extra slots or favor recency.

Once a component already has direct coverage, additional distinct results may still be useful: e.g. model cost reduction and approval latency are not redundant because both relate to AI delivery. Selection must not degenerate into one bullet per requirement or one per system.

First writer request contains:

- Role and raw JD; all component IDs, importance and target skills.
- Full document outline, all candidate IDs and their planned purposes.
- Source text/fact IDs, metric scopes, status and relevant restrictions for each candidate.
- Approved skill groups, fixed identity/dates/education.
- One selected independent prototype story; local scope and absent dates/URL/metrics.
- Summary instructions: two or three substantive sentences covering role identity, relevant breadth, kinds of work solved and central implementation tools. Aim roughly 55-80 words, subject to the page. This is writing guidance, not a lower/upper word-count gate or another evaluator.
- Bullet instructions: one useful accomplishment with enough detail to understand action, technical mechanism and consequence. Usually 20-40 words; permit more when necessary. Remove old hard 32/38 limits. No fragments merely to hit a count, no forced verbosity.
- Letter instructions: three developed paragraphs, normally about 220-300 words in total. Opening connects the particular role to candidate breadth; middle develops one example; closing states a specific prospective contribution. No word-count-triggered repair or duplicated case study. Letter length does not consume resume space.

The writer returns a dictionary of texts for supplied IDs. It does not select evidence, score itself, decide layout or write Skills from memory. One coherent initial creation call; no employer-isolated prose generation. Use the existing writer unless a later explicit experiment changes it. Transport/token configuration must support this larger response; fail clearly on truncation, never accept an incomplete set of IDs.

## 6. One-page selection using actual space

Keep current page size, margins and readable typography. Do not build a page-density semantic gate or use word count as the page-fit proxy.

Draft up to four useful bullet candidates per employer once; mark optional alternatives in the internal blueprint. Measure the actual ReportLab flowables, using the same widths, fonts, leading, spacers and grouping as final rendering. Reserve identity, summary, all Skills, all employer headings, one project with two concise bullets and education. Candidate metrics/status already passed their leaf checks or are explicitly failed/unresolved.

Select an experience subset with 1-4 bullets per employer that fits the measured remaining space. There are at most 65,536 subsets of sixteen candidates; code can enumerate them cheaply without inference. Score feasible subsets lexicographically by visibly direct core-component coverage, partial core-component coverage, supporting-component coverage, distinct relevant accomplishments and stable ID order. Scores come from recorded per-item Jev outcomes, not writer guesses. Full-page use results from including additional distinct useful evidence when it fits; there is no arbitrary minimum fill percentage.

Preserve summary/skills/project instead of sacrificing those sections to pack sixteen experience bullets. Each omission is recorded as redundant/incidental/page space/failed candidate; useful unused evidence and affected coverage remain in the report. Failed/unresolved required content may not be dropped solely to get a green status. If the required sections plus one bullet per employer do not fit, create a `PAGE_OVERFLOW` issue listing exact measured excess and the largest eligible prose blocks. It shares the same two repair rounds; no separate layout loop. If still impossible, output REVIEW_REQUIRED with the reason.

Selected full-document rendering and page count are authoritative if flowable prediction disagrees. Do not silently reduce fonts or trust an approximate additive height for KeepTogether/spacing behavior. After repairs remeasure and recompute the selected subset from the existing candidates; no new candidate generation just for page fullness.

## 7. Jev hierarchy and acceptance

All nodes have IDs, type, parent ID, source dependencies and current content hashes. Implement explicit node lists and functions; no generic recursive-agent framework.

| Level | Separate questions | Context provided |
|---|---|---|
| JD component | faithful quote/meaning; priority; work vs tool | component + its JD passage; original JD for omission check |
| Skill item | type; relevance; specificity; group fit | item + JD passage + fixed type/group choices |
| Skill group | coherent label/membership; duplicates | label + examined children + item decisions |
| Skills section | relevant completeness; cross-group overlap | groups + whole classified stack |
| Experience bullet | action/mechanism/consequence; assigned component; clarity; status/metric scope | exact system facts, purpose and sentence |
| Employer | useful breadth for its JD contribution; distinct accomplishments; consistent scope | its current bullets, source systems and available omitted candidates |
| Experience section | distinct value across employers; allocation does not bury stronger relevant work | current employers + remaining useful candidates + component coverage |
| Project bullet | local workflow, useful output and functional target stack | project pattern + selected workflow + local restrictions |
| Project | clear independent work; direct JD purpose; distinct angle from employment | project + employment examples + JD components |
| Summary sentence | role-relevant positioning; clear concrete meaning; legitimate scope | sentence + identity/selected evidence + JD |
| Summary | coherent professional overview without repeating detailed achievement | summary sentences + resume outline |
| Letter paragraph | its assigned role; specific work/reason; readable prose | paragraph + planned purpose + permitted example |
| Letter | developed argument; no repeated case study or generic closing | three checked paragraphs + role/company JD |
| Application | cross-section contradictions, unnecessary story repetition and visible work coverage | final displayed texts + all child/parent decisions |

Use PASS/FAIL/UNCERTAIN for specific checks, fixed semantic kinds for classifications, DISTINCT/REDUNDANT/CONTRADICTORY/UNCERTAIN for relationships. Parent reports list constituent IDs; a failure without a uniquely actionable target remains unresolved and stops automatic repair of that issue. Pair questions identify redundant items. For employer breadth, each omitted distinct candidate is asked whether it contributes MATERIAL_VALUE/NO_ADDED_VALUE/UNCERTAIN beyond its current selected employer text. These answers can influence the deterministic subset ranking in the same existing revision; they cannot add a fifth candidate or launch a fresh writer round.

Each unique supported required component is checked against the actual final bullet IDs. Report Explicit/Partial/Missing/Uncertain. A component missing from every selected source is still Missing; exclude neither planning gaps nor unsupported core requirements from the final table. Partial is never relabeled as full coverage. A core work component Partial/Missing/Uncertain keeps REVIEW_REQUIRED; optional preferences are informational. No hard job-rejection agent is added.

Employer material-value answers are cached for the current candidate/selected-set hashes. At most one deterministic reallocation per draft revision uses those answers. Newly selected content receives its required parent checks before export; another parent's dissatisfaction remains a reported issue or enters the existing repair budget, never an unbounded reallocation loop.

Repetition policy:

- A central tool in Skills and again in Experience is useful reinforcement.
- A capability in Summary and a concrete demonstration in Experience is allowed.
- A resume example developed in the letter is allowed.
- Two accomplishments from one system are allowed when work/consequences differ.
- Repeating the same accomplishment within Experience or retelling the letter proof in the opening is redundant.
- A local project can share architecture with employer work; it must explain the local problem/output and a useful technical angle rather than copying employer bullets/scale.

Final status predicate: all required current leaf decisions pass, all required parent decisions pass, no required unresolved issue, no missing/partial/uncertain core component, identity/schema checks pass and final PDFs fit. A global PASS never overrides a failed leaf. Fix the current pipeline gap where `release_status` receives global verdicts and block statuses but not the complete `assessment.passed`/unresolved/coverage result.

## 8. Repairs, caching and cost

Retain initial + two repair rounds TOTAL. One shared per-ID attempt count, including malformed creation responses and local/parent issues; no automatic budget reset on parent changes or process restart. `UNCHANGED` cannot resolve an unchanged failure. Do not loop over a hierarchy with its own retries at each level.

Collect all failures into one issue table. Deterministic corrections (exact spelling, grouping from confirmed type, moving an item, removing duplicate aliases) are code actions and are persisted before rechecking affected parents. Prose repairs use one writer call per round with exact writable IDs, the complete draft read-only and relevant source facts. Do not ask the writer to decide which candidate to keep or produce a verdict. A parent issue targeting multiple children shares the same round, not one round per child.

Cache each Jev answer by its exact question, options, policy version and relevant dependency hashes. Changing one bullet invalidates that bullet, its employer, relevant requirement/pair checks and ancestors; it does not rerun another employer's leaf checks or every skill. Questions are grouped in existing bounded requests (40 questions/approximately 75,000 serialized characters); an oversized single case fails explicitly with its size rather than bypassing the limit. Keep max_requests=80 for the first v3 experiment; exhaustion preserves the draft and visible reason. Do not raise it silently or promise an exact runtime/cost before measuring.

Persist phase/cursor/targets/issue IDs and stage usage BEFORE calls. On resume, consume a saved pending response before planning a new call. Planning usage also needs persisted `begin_stage`, not the current in-memory snapshot. Timing must label wall elapsed across interruptions accurately.

## 9. Product output

Same public root schema. `resume.projects` now accepts one real Project object in v3, using the existing renderer shape `{name, period, bullets}`; period may be empty. Preserve v1/v2 empty project support for offline rendering. No invented new project URL field; confirmed profile GitHub link remains optional.

Internal output stays deeply structured; export flattens approved skill groups to `{label,value}` and bullet texts to existing arrays only at the end. The public renderer contract must not force flat internal reasoning.

Save `coverage.md` and matching JSON with:

- JD component -> priority -> final employer/project/bullet -> Explicit/Partial/Missing/Uncertain.
- JD technology -> item kind -> group -> exact displayed occurrences.
- Employer -> selected bullet count -> useful candidates omitted and why.
- Project -> JD purpose -> independent/local scope.
- Specific outstanding issues with affected text, not only PASS/FAIL counts.
- Page count/font/parse checks labelled local PDF checks, never 'ATS passed'.
- Actual writer calls, Jev HTTP calls, logical Jev question count, retries, total cost and elapsed time. Show preparation and writing costs separately.

CLI progress shows plain stages and actionable outcomes. No claim that a one-page PDF or Jev PASS predicts interviews. User-facing completion shows the PDFs first, a short coverage summary and remaining issues; no blind-review request is a substitute for fixing the known document requirements.

## 10. Handoff stopping point

Sol may implement this exact design, tests, fixtures, migration and a local layout preview. Before any paid v3 run it must show the source migration coverage, the planned Skills hierarchy and employer/project structure, plus the offline test result. Then the already-authorized Stibo/McKesson experiments may run if the user continuation includes execution; do not pay for repeated tuning. Stop after one v3 run per selected JD and preserve failures. New structural choices (taxonomy expansion, relaxed gates, changed page count, provider swap, more retry rounds) return to the user with one concrete decision.

Quality cannot be guaranteed in advance. The handoff prevents silent interpretation changes through explicit contracts and observable acceptance tests; it does not promise Sol or any model cannot make mistakes.
