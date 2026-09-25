"""Build a review map of the preserved agreement, without changing the application."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from project_memory.store import Store

OUT = ROOT / 'project-memory' / 'maps'
s = Store(ROOT)


def n(id, title, points=(), children=(), src=(), routes=(), state='Agreed design; implementation not certified here'):
    return dict(id=id, title=title, points=list(points), children=list(children), sources=list(src), routes=list(routes), state=state)


application = n('application', 'Layer 1 · The application that creates your documents', [
    'Input: a pasted JD plus your canonical and application policies.',
    'Output: resume PDF, cover-letter PDF, application JSON, portable chat context, coverage/issues and trace.',
    'Routine generation asks no approval questions. Missing setup information identifies the exact field to edit.'
], src=[1,21,29], children=[
 n('data', 'A · Three separate kinds of application data', children=[
  n('canonical', 'Canonical · Your work, split into linked records', [
   'The agreed physical starting point is one authoritative canonical.yaml containing typed records. Separate records do not require competing copies of the same facts.',
   'The context graph must also expose these branches individually. Opening Canonical must not force a model to read all employers and systems.',
   'Only your factual additions/corrections change canonical facts. A JD or generated sentence never becomes a fact automatically.',
   'Split by coherent meaning. Keep connected workflow actions together; separate genuinely distinct accomplishments.'
  ], src=[3], routes=[['context','How the coding agent retrieves these branches'],['packet','How selected facts become model inputs']], children=[
   n('profile', 'Profile, contact and education', ['Stable identity/contact records; education records. Python copies fixed details into the documents.'], src=[3,24]),
   n('identity', 'Professional identity', ['The professional framing used by summary and selection; distinct from employer chronology.'], src=[3,9]),
   n('employers', 'Employers → each employer has its own branch', ['Stable employer ID, company, titles, dates and employment status. All four employers remain in the resume.'], src=[3,6], children=[
    n('systems', 'Employer → systems / initiatives', ['Each system has its own purpose and original narrative, preserving the surrounding meaning. Do not combine unrelated initiatives.'], src=[3], children=[
     n('facts', 'System → typed facts', ['Problem: what needed solving.', 'Inputs: documents, events, records or other material.', 'Actions: what you built, changed or operated.', 'Outputs: the artifact or behavior produced.', 'Outcomes: what changed operationally.', 'Implementation status: actual stage of the work.'], src=[3]),
     n('metrics', 'System → metrics', ['Value, meaning, scope and achieved-versus-target status.', 'A metric stays attached to the work it describes; no transfer between projects.'], src=[3]),
     n('boundaries', 'System → boundaries', ['Ownership, deployment status and qualifications.', 'A local prototype must not become a production claim.'], src=[3]),
     n('accomplishments', 'System → distinct accomplishments', ['Each accomplishment links a compatible set of facts, metrics and boundaries.', 'Building a workflow, improving operation and enabling adoption can be distinct achievements; renaming the same achievement does not create breadth.'], src=[3]),
     n('provenance', 'Each fact / accomplishment → source passage', ['Stable source reference and exact original passage.', 'Keep provenance reachable without injecting the entire canonical into every request.'], src=[3])
    ])
   ]),
   n('prototype-pattern', 'Independent project / local prototype pattern', ['Your local/GitHub working pattern is represented separately.', 'Use compatible JD-specific retrofit; no exhaustive inventory of every project is required.', 'Do not fabricate repository URLs, dates, employer-scale results or production deployment.'], src=[3,8])
  ]),
  n('policy', 'Policy · Rules stay separate from facts', ['Retrofit permission; writing preferences; structure and limits; taxonomy and check policy; layout, repairs and stopping rules.', 'Changing a policy does not rewrite canonical history.'], src=[3,4,23], children=[
   n('retrofit', 'Technology retrofit → functional placement', ['Work determines relevance; employer-specific historical tool matching is not required.', 'No exhaustive technology questionnaire or repeated justification of permission.', 'For each tool, Jev receives target technology, original JD passage, workflow stages and proposed role.', 'Choices: FUNCTIONAL / MISPLACED / UNNECESSARY / UNCERTAIN.', 'No default FUNCTIONAL and no first-three-technologies shortcut.'], src=[4]),
   n('structure', 'Document structure and readable writing', ['All four employers; at most four bullets each; no eight-total cap and no forced four-bullet quota.', 'Required relevant independent project; developed short summary; readable grouped skills.', 'One or two pages, including one-and-a-half; preserve useful content, readable type and spacing.', 'Word ranges guide writing; they are not rejection gates. No padding merely to fill a page.', 'Fixed companies/dates stay fixed; no fabricated metrics, names or links.'], src=[6,8,9,11,23])
  ]),
  n('run-data', 'Run data · One application, kept separate', ['Original JD/hash; requirement interpretations; evidence selection and omission reasons; skills and project brief.', 'Writer inputs, saved text blocks, revisions, check results, final artifacts and unresolved issues.', 'Input/configuration/prompt/rubric/model versions; request/response references; code version.', 'Run history does not bloat the canonical.'], src=[3,13,21,27])
 ]),
 n('jd', 'B · JD → traceable requirements', ['Save exact text and hash → Python passage IDs and offsets → account for every nonblank source span.', 'In parallel: Jev passage classification and one structured extraction request.', 'Classification: work, qualification, technology, company context, mixed or uncertain.', 'Python verifies quotes/IDs; Jev checks the interpretation against original passages.', 'Each requirement: source passage, interpretation, priority, meaningful child components, named technologies, unresolved interpretation.', 'Invalid/missing interpretation → retain original passage and mark unresolved; do not repeatedly regenerate extraction.', 'Compound requirements remain unresolved until their meaningful components are accounted for.'], src=[5], routes=[['selection','Use requirements to select work'],['coverage','Compare requirements with final sentences']]),
 n('brief', 'C · Select work → assemble the complete writing brief', children=[
  n('selection', 'Select accomplishments for each employer', ['Jev checks work relevance, exact requirement support, specificity, duplicate pairs and technology placement.', 'Support: direct / partial / adjacent / no support / uncertain.', 'Python selects central work first, distinct supporting work next, concrete evidence, then removes genuine repetition.', 'Older employers can receive substantial space. Recency does not automatically dominate.', 'Record a reason for every exclusion. Use the two-page amendment rather than the retired one-page subset optimization.'], src=[6,23], routes=[['canonical','Retrieve the matching work records']]),
  n('packet', 'Resolve IDs → actual evidence text', ['For each candidate: employer/system, original narrative, problem/inputs, actions/outputs, relevant outcome, permitted metric, status/boundaries, assigned JD requirement, placed technologies and intended point.', 'Python resolves references. Both writer and Jev receive the actual evidence, not unexplained fact IDs.'], src=[2,3,9]),
  n('skills', 'Skills → each term → each group → whole section', ['Internal classification differs from displayed resume groups. Necessary repetition between Skills and Experience is allowed.'], src=[7], children=[
   n('taxonomy', 'Classify individual terms', ['Language: Python / TypeScript / SQL.', 'Framework/library: LangGraph / LangChain. Provider: OpenAI.', 'Cloud service: Azure AI Services. Database: PostgreSQL.', 'Deployment tooling: Docker / Kubernetes. Practice: CI/CD.', 'Architecture: RAG. Broad discipline: MLOps, only with useful context. Model family: LLMs.', 'Examples illustrate types; they are not mandatory insertions. Do not invent a model name when the JD only says LLMs.'], src=[7]),
   n('skill-checks', 'Term and subterm checks', ['Type → JD relevance → meaningful specificity → group membership.', 'Do not label AI, automation and MLOps as concrete products.'], src=[7,10]),
   n('skill-groups', 'Group and section checks', ['Every group: members fit label and avoid duplication.', 'Whole section: important relevant terms without irrelevant clutter.', 'Python assembles approved groups; Jev answers individual semantic questions.'], src=[7,10,24])
  ]),
  n('project-brief', 'Independent project → explicit workflow', ['Purpose tied to a JD capability; relationship to your work and authorized prototype pattern.', 'Input → concrete steps → technologies with specific roles → inspectable output → validation.', 'Explicit local/independent scale; confirmed GitHub pattern without invented repository URL.', 'Jev evaluates relevance; Python selects by purpose, not the first employer/candidate.', 'Writer produces a concrete title and normally two complementary bullets: behavior, then output/validation.'], src=[8], routes=[['prototype-pattern','Retrieve authorized project pattern']])
 ]),
 n('writing', 'D · Fill the resume and letter with owned text blocks', ['Current design recommendation: one coordinated initial writing request, then independent block repairs. Separate ownership does not mean a model call for every block.', 'Separate initial section writers remain a possible later experiment, not a proven improvement.', 'Python copies name/contact/employers/titles/dates/education and assembles skills.', 'Writer chooses wording, structure and emphasis within supplied facts. It does not change employers, invent metrics or grade itself.', 'Save JSON and PDF previews early; the user can inspect the draft while checks are pending.'], src=[9,24], children=[
  n('blocks', 'Each writing unit has its own record', ['Block ID; parent employer/section; assigned point; resolved evidence; JD responsibility; technology placement; writing instruction; current text; check results; revision history.'], src=[24]),
  n('resume-blocks', 'Resume blocks', ['Summary: professional identity, relevant systems and scope in a developed short paragraph.', 'Each of four employers: up to four distinct accomplishments, each with mechanism and output/result.', 'Project: concrete independent workflow, output and validation.', 'A number is optional; supported specific actions are essential.'], src=[9,24]),
  n('letter-blocks', 'Cover-letter blocks', ['Opening: specific role connected to relevant work.', 'Middle: develop a strong example rather than a skills list.', 'Closing: concrete prospective contribution and direct close.'], src=[9,24])
 ]),
 n('review', 'E · Review from the smallest item upwards', ['Independent questions within a level can share one Jev request. Parent levels consume completed child results.', 'One Jev API serves these questions; no separately deployed evaluator per box.', 'A parent PASS cannot erase a failed child. An unexplained subjective failure becomes unresolved, not a speculative full rewrite.'], src=[10,24], children=[
  n('review-paths', 'Four review paths → document consistency', ['Skill term → group → Skills section.', 'Experience bullet: meaning, clarity, evidence, scope, JD purpose → employer breadth/distinctness/scope → Experience section.', 'Project bullet: local scope/workflow/output/clarity → coherent whole project.', 'Summary sentence / letter paragraph: purpose/specificity/clarity → whole summary / whole letter.', 'Completed section results → final visible application: consistency, coverage and unnecessary repetition.'], src=[10]),
  n('decision-log', 'Save each judgment', ['Item, dimension, exact question and answer choices, supplied evidence, selected answer, model/policy versions, input hash, cache state and affected output IDs.'], src=[10]),
  n('coverage', 'Coverage must refer to final visible sentences', ['Explicit / partial / implied / missing / uncertain.', 'Link every claim to actual visible text. Removed bullets cannot contribute coverage.', 'Unresolved interpretations stay visible. Planned candidate coverage is insufficient.'], src=[2,5,11])
 ]),
 n('layout', 'F · Render and inspect one or two pages', ['Measure with actual renderer typography and flowables; preserve all mandatory sections and useful content.', 'Keep readable fonts/spacing and prevent stranded headings. No silent font shrinking.', 'If three pages: inspect formatting, duplication and verbose wording first. If still too long, preserve draft and report it.', 'Never remove the project or employer; never shorten the letter to solve resume overflow.', 'Use actual PDF pagination/page images; text judgments cannot certify layout.', 'Final rendering/repair changes feed back into final-text coverage. The old one-page subset search is superseded.'], src=[11,14,23], routes=[['coverage','Recheck final visible text'],['repairs','Local repair if necessary']]),
 n('repairs', 'G · Targeted repairs with a shared limit', ['Budget: one extraction, one complete draft, at most two shared repair rounds. Malformed drafts consume the same writing allowance.', 'Missing evidence → fix assembly. Wrong group → regroup. Misplaced tool → correct placement. Vague sentence → rewrite using evidence.', 'Duplicate → replace/remove weaker duplicate. Missing coverage → identify eligible supporting content. Overflow → affected document only.', 'Ambiguity → retain draft/report uncertainty. Timeout → preserve progress; only transport-policy retry.', 'Repair receives the affected block, evidence/instructions and read-only neighboring text. Python rejects edits to other IDs.', 'Changed bullet invalidates its own checks, employer, related requirements and document dependencies; unrelated unchanged checks stay cached.', 'Cache key includes evidence, text, question, policy and model. No loop until PASS.'], src=[12,24]),
 n('app-observe', 'H · Application visibility, stopping and replay', children=[
  n('events', 'Every stage/request → local event journal', ['Run/parent/stage/batch/request IDs; operation; endpoint/model; start/end/status; input/output references.', 'Input size/question count; cache state; attempt/repair count; returned usage; error category; resumable checkpoint.', 'Keep credentials out; no claim to hidden model reasoning. Missing usage is unknown.'], src=[13]),
  n('live', 'Live view → what is happening now', ['Current stage/model/request; elapsed time and deadline; cached/executing/failed/retrying.', 'Completed work and available inputs/drafts/evidence; affected repair block and why; Stop/Open inputs/Open draft/View events.', 'Python refreshes timers locally, without model polling. Distinguish slow progress from repeated no progress.'], src=[13,25,27]),
  n('trace-stack', 'Tools and responsibilities', ['Existing Python executes; Pydantic validates record shapes.', 'Append-only local JSONL is authoritative. Local terminal shows progress.', 'Langfuse is the planned optional trace explorer; deployment not established here. Export must not block generation.', 'LangChain is not required. Recorded responses support deterministic replay without new model calls.'], src=[25,27]),
  n('deadlines', 'Deadline / cancel / resume', ['Proposed configurable initial limits: Jev request 20 seconds, writing request 120 seconds, application eight minutes.', 'Enforce deadlines outside model calls; socket timeout alone is insufficient.', 'Cancel preserves completed work; interrupted upstream requests may still be billed.', 'Repeated identical outputs/failures or exhausted repair budget → explicit stop.'], src=[13,27]),
  n('post-run', 'Afterwards → trace the exact fault', ['Artifacts; stage durations; failures/retries; revision differences; selected/omitted work and reasons.', 'Requirement-to-sentence coverage; unresolved issues; exact requests/responses/sources.', 'Snapshot inputs/configuration, prompt/rubric/model and code versions.', 'Example trace: project brief → writer response → JSON → PDF identifies where a project disappeared.'], src=[13,25,27])
 ]),
 n('evaluation', 'I · Check software, evaluator and actual product separately', ['Mechanical correctness: structure, identities, references and layout constraints.', 'Jev accuracy: false approvals, false rejections, uncertainty and disagreement with confirmed feedback.', 'Product quality: readable, useful, JD-tailored output judged from real artifacts.', 'Use existing evaluation tooling with Python/Jev adapters, not another evaluation platform.'], src=[14], children=[
  n('cases', 'Cases from actual complaints, plus acceptable examples', ['Thin summary; flat skills; methods mislabeled as products; generic AI vocabulary.', 'Missing project; older employers squeezed; eight-total truncation; repetition; relevant work omitted.', 'Invisible-content coverage; metrics on the wrong work; weak letter paragraphs.', 'Each case: original JD, actual excerpt, complaint/rule, expected judgment, reason, confirmed/provisional label.', 'Acceptable examples prevent reject-everything scoring. No demand for hundreds of labels or a perfect resume.'], src=[14])
 ]),
 n('deliverables', 'J · Deliver the package with an honest status', ['Resume PDF; cover-letter PDF; application JSON; portable context; readable coverage/issues; trace/revisions.', 'Portable context: JD, generated text, relevant canonical excerpts, retrofit policy and outstanding issues.', 'Draft = checks pending. Ready under configured checks = configured checks completed, not a guarantee of recruiter response.', 'Review required = named unresolved issues. Stopped = last checkpoint and reason.'], src=[21])
])

context = n('context', 'Layer 2 · The external context used by you and the coding agent', [
 'The application is what we build. This layer stores how it is designed, where work stands, what changed and the evidence.',
 'Any capable CLI/agent can read the same local records and use the Python tool. No required model and no reliance on this conversation.',
 'A small startup pointer opens the graph. A full plan archive is evidence, not the default context loaded every session.'
], src=[1,15,29], state='Storage/basic retrieval built; detailed semantic graph still incomplete', children=[
 n('entry', '1 · New session → orient both the agent and you', ['Read NOW.md / MEMORY.md → run start → current checkpoint + essential active rules.', 'Explain goal, completed stages, current task and next action in plain language, assuming no chat context.', 'Open only current component and needed children; follow named links for more detail.', 'A question asks for an explanation; it must not silently become an implementation request.'], routes=[['memory-structure','What is stored'],['human','How you steer']]),
 n('memory-structure', '2 · Split the stored context by responsibility', children=[
  n('root', 'Project root → small map', ['Goal; active checkpoint; compact global rules; directory of all application components.', 'Every Layer 1 branch has its own context route, including Canonical → employer → system → individual evidence records.'], routes=[['canonical','The canonical must be split too']]),
  n('component', 'Component → children → detail', ['Each component: purpose, ownership, inputs, outputs, status and index of child summaries.', 'Each child: one coherent rule, requirement, design decision or task; enough standalone explanation to make sense without chat.', 'Named routes explain when to follow: part_of / depends_on / uses / based_on / supersedes.', 'Shared rules/facts are linked rather than copied into every branch.']),
  n('record', 'Every context record', ['Stable ID; title/summary; standalone detail; owning component; active status; applicable rules.', 'Named connections; exact source references; revision; timestamp; reason for change.', 'Distinguish planned behavior, observed implementation and user-accepted result.']),
  n('storage', 'Portable storage and retrieval', ['Authoritative versioned JSON records; SQLite is a rebuildable search/relationship index.', 'CLI: start/context, show, source, search, impact, put, timeline, doctor, view.', 'Preserved source text → exact passages. Old revisions stay reachable but are not all loaded.', 'Current commands and broad module records exist. Complete semantic child decomposition and coverage mapping are still outstanding.'], state='Existing storage/basic commands; semantic expansion pending'),
  n('history', 'Current state separate from dated history', ['Current active rules remain applicable even when a newer topic gets attention.', 'Explicit supersedes links replace a decision; a timestamp alone does not.', 'Record meaningful decisions, feedback and outcomes before dependent work; not every conversational sentence.', 'Routine event logs remain separate from compact current records. Local logs survive local sessions but are not automatically in a Git clone.'])
 ]),
 n('task', '3 · One bounded coding task at a time', ['Record the user requirement, exact failure/example, expected behavior, relevant component and allowed files.', 'Preserve evaluation/reference version, required evidence, stop conditions and paused checkpoint before editing.', 'Read relevant graph branches rather than replaying the entire chat. Do not silently change settled scope.', 'Implementation result = diff, actual command results, examples and failures; a completion message alone is not acceptance.', 'Earlier Astra/Sol/Terra assignments are historical. Roles may be performed by any capable selected agent; extra agents are not mandatory.'], src=[15,17,19], children=[
  n('verification', 'Verification → evidence for your review', ['Python: files exist; matching code revision; commands really ran; references preserved; allowed scope and limits.', 'Jev: narrow obligations with actual evidence; SATISFIED / VIOLATED / INSUFFICIENT_EVIDENCE.', 'Example: removed bullet still counted? final selected content used? requirement weakened? unrelated behavior changed?', 'Jev does not execute commands, grant scope expansion or certify arbitrary code from a diff.', 'Missing evidence calls for that evidence, not a rewrite. Technical results are separate from your acceptance.'], src=[16,17]),
  n('coding-limits', 'Resource and stop rules', ['Small context; one task per worker; no recursive spawning or repeated model status polling.', 'Focused checks for a local change; broader regression at integration.', 'Original proposed worker deadline: 20 minutes, with saved progress; not certified as enforced.', 'No automatic restart or credit purchase. Record attempts, waiting/execution time and available usage.', 'Account allowance is separate from per-task usage; no invented credit accounting.'], src=[19])
 ]),
 n('change', '4 · Feedback or new idea → controlled update', ['Attach feedback to exact output/revision and affected node; preserve the paused task.', 'Inspect evidence, selection, writer input and judgments. Diagnose the earliest demonstrated failure.', 'Change the smallest relevant record/module; inspect linked dependencies and actual interfaces for downstream effects.', 'Explain consequential cross-component changes before expanding scope. Do not quietly rewrite unrelated checkpoints.', 'Replay the affected example, compare before/after, protect previously acceptable examples.', 'Repeated failure stops the same repair path; bring the evidence back for a design decision, without a required model brand.'], src=[18], children=[
  n('human', 'Your ordinary words → expected handling', ['“Why this project?” → show saved reason; change nothing.', '“This bullet is vague” → inspect that block and diagnose.', '“Try another summary” → keep old version and create revision.', '“Allow two pages” → policy and affected layout/checks; no factual rewrite.', '“Different architecture” → record design change and affected components.', '“Stop” → stop execution and preserve progress.', 'No special prompt syntax required. Clarify consequential ambiguity; do not require you to know internal machinery.', 'You inspect real results and decide acceptance. A question or technical PASS is not acceptance.'], src=[28])
 ]),
 n('coding-observe', '5 · Observe the coding work and connect it to runs', ['Task/requirement version → agent/session → commands/diff → verification/judgments → commit/result.', 'An application run records the code version, connecting this development timeline to the separate application timeline.', 'Live status: task/model, outstanding work, elapsed/deadline, attempts, evidence and last saved result.', 'Afterwards: exact changed files, why, results, unresolved issues and next action.', 'Use local journals as durable records. Automatic tool capture needs a host-specific adapter; shared semantic records remain portable.', 'Codex hook configuration exists but live delivery was not established. Other tools do not inherit Codex hooks.', 'No hidden reasoning capture. Save decisions explicitly; event hooks cannot infer their meaning.'], src=[13,25], routes=[['app-observe','Separate application-run visibility']], state='Memory events/views built; automatic host capture not certified'),
 n('commits', '6 · Record → refresh tracker → one coherent commit', ['Commit meaningful design/behavior/checkpoint changes separately; do not bundle unrelated fixes.', 'Label with task/issue plus short problem, change, evidence and scope. Git supplies ID/time.', 'Trace: task → issue/example → change → commit → application run.', 'Preserve starting checkpoint; label unfinished work honestly; update current state/next action before a new session.', 'Keep credentials and private generated application payloads out of Git; link local evidence.', 'PR only when useful/authorized; a local commit does not require publication. Revert a specific change when appropriate.', 'Temporal here means versioned history over time, not installing the Temporal platform.'], src=[26,27]),
 n('checkpoints', '7 · Current project checkpoints', [], state='Read from current saved records'),
 n('legacy', '8 · Preserved history and amendments', ['Original model-locked coding diagram is historical; no mandatory Astra/Sol/Terra handoff.', 'One-page-only fitting and expensive subset selection are superseded by one/two-page content priority.', 'Original implementation ordering is retained for reference; current checkpoint records control the current task.', 'Separate block ownership is retained; one coordinated initial call remains the recommendation, not a proven quality result.', 'User feedback is preserved verbatim, including questions and provisional acceptance; not every recommendation becomes implementation evidence.'], src=[20,22,23,24,29])
])

def walk(node):
    yield node
    for c in node['children']:
        yield from walk(c)

canonical_node = next(x for x in walk(application) if x['id'] == 'canonical')
canonical_node['state'] = 'Typed canonical.yaml exists; detailed coding-context routes remain incomplete'
canonical_node['children'].append(n('actual-canonical', 'Existing YAML · field structure and system directory', [
 'Observed stored schema, not proof that all content is correctly extracted or used.',
 'Policies currently live inside canonical.yaml; conceptual separation does not imply separate physical files are implemented.',
 'Identity and administrative values include prose. Technology examples are not yet a normalized tool-node inventory.'
], state='Observed stored structure', children=[
 n('canonical-root-fields', 'Root, identity and administrative fields', [
  'Root: schema_version, source_archive, source_archive_sha256, profile, education, identity, administrative, policies, employers, facts, metrics, boundaries, prototype_pattern, migration.',
  'profile: name, phone, location. education[]: degree, school, year.',
  'identity: professional_spine, career_progression, maintainability, claim_boundaries.',
  'administrative: citizenship, immigration_status, relocation, work_authorization_rules, known_technology_examples.',
  'policies: stack_retrofit, max_bullets_per_employer, include_independent_project.'
 ], state='Observed stored fields'),
 n('canonical-work-fields', 'Employer, system and accomplishment fields', [
  'employer: id, company, titles[], period, status_text, boundary_ids[], systems[].',
  'system: id, narrative, source_refs[], problem_fact_ids[], input_fact_ids[], action_fact_ids[], output_fact_ids[], outcome_fact_ids[], status_fact_ids[], metric_ids[], boundary_ids[], accomplishments[].',
  'accomplishment: id, system_id, purpose, fact_ids[], metric_ids[], boundary_ids[].',
  'Inventory: 4 employers, 19 systems, 19 accomplishments, 57 facts, 12 metrics, 4 boundaries, 2 education entries, 63 migration mappings.'
 ], state='Observed stored fields'),
 n('canonical-evidence-fields', 'Evidence, source and migration fields', [
  'fact: id, employer_id, system_id, kind, text, source_refs[]. Kinds: problem/input/action/output/outcome/status.',
  'metric: id, employer_id, system_id, display_text, meaning, status, source_refs[]. Status: achieved/target/derived.',
  'boundary: id, scope_ids[], text, source_refs[].',
  'SourceRef: archive_sha256, start_line, end_line, quote.',
  'prototype_pattern: statement, local_scope, publication_status, source_session_note, restrictions[], metric_ids[].',
  'migration: start_line, end_line, destination_ids[], disposition (structured/archived/superseded).'
 ], state='Observed stored fields'),
 n('canonical-system-directory', 'Employer → current system IDs', [
  'corominas → corominas.multi_tenant; corominas.llm_harness; corominas.quality_gate; corominas.approval; corominas.agent_ops; corominas.generated_workflows; corominas.security_response.',
  'formula_dream → formula.event_pipeline; formula.workflow_generator; formula.event_templates; formula.information_aggregation; formula.formulytics.',
  'think_round → think.context_memory; think.safety_evaluation; think.multi_agent_platform.',
  'cognizant → cognizant.ingestion; cognizant.kpi_latency; cognizant.aws_etl; cognizant.data_quality.',
  'Each system currently has one accomplishment: <system-id>.accomplishment.'
 ], state='Observed IDs; not yet individually indexed coding-context nodes')
]))
project = s.get('project')
cp = next(x for x in walk(context) if x['id'] == 'checkpoints')
cp['points'] = [f"{s.get(i)['title']} — {s.get(i).get('status') or 'not started'}" for i in project['checkpoints']]
cp['points'] += ['The graph map is a review artifact. It does not mark the application, coding controls or fine-grained memory migration complete.']
raw = (ROOT / 'project-memory/sources/source-agreement.txt').read_bytes()
original = raw.decode('utf-8-sig')
lines = original.splitlines(keepends=True)
sections = []
for i in range(1, 30):
    record = s.get(f'source-agreement-{i:03}')
    ref = record['sources'][0]
    sections.append(dict(number=i, id=record['id'], title=record['title'], start=ref['start'], end=ref['end'], text=''.join(lines[ref['start']-1:ref['end']])))
assert ''.join(x['text'] for x in sections) == original, 'Source sections must preserve the complete agreement'
all_nodes = list(walk(application)) + list(walk(context))
ids = {x['id'] for x in all_nodes}
assert len(ids) == len(all_nodes)
assert set(range(1,30)) == {i for x in all_nodes for i in x['sources']}
assert all(target in ids for x in all_nodes for target, _ in x['routes'])
record_ids = ['project', 'checkpoint-memory', 'blueprint-semantic-context-graph', 'decision-superseded', 'decision-modular-temporal-memory', 'rule-scope', 'rule-collaboration', 'rule-memory', 'rule-changes', 'rule-application', 'rule-observations', 'state-existing-code']
data = dict(title='One project, two separate layers', layers=[application,context], sections=sections,
            current_records=[s.get(i) for i in record_ids],
            source_sha256=hashlib.sha256(raw).hexdigest(),
            canonical_sha256=hashlib.sha256((ROOT / 'canonical.yaml').read_bytes()).hexdigest(),
            source_coverage={str(i): [x['id'] for x in all_nodes if i in x['sources']] for i in range(1,30)},
            scope='Map of saved agreement and current context design; not an implementation certification.',
            current_request='2026-09-25: Show both layers and every internal branch, including the canonical, for Lohith to judge. Do not stop at a shallow component directory.')
OUT.mkdir(exist_ok=True)
(OUT / 'two-layer-plan.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
template = (OUT / 'two-layer-map.template.html').read_text(encoding='utf-8')
payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
result = template.replace('/*PLAN_DATA*/null', payload)
(OUT / 'two-layer-map.html').write_text(result, encoding='utf-8')
print(json.dumps({'nodes':len(all_nodes), 'agreement_sections':len(sections), 'agreement_complete':True, 'links_valid':True, 'bytes':len(result.encode('utf-8')), 'limitation':'Source preservation and link integrity, not independent certification of every summary.'}))
