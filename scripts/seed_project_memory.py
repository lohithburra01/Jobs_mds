"""One-time migration of existing agreement and context. Never resets a live project."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_memory.store import Store
from project_memory.views import dashboard

ROOT = Path(__file__).resolve().parents[1]


def seed():
    s = Store(ROOT)
    if (s.home / "records" / "project").exists():
        raise ValueError("Project already seeded. Use versioned put; do not rerun the bootstrap over live decisions.")

    def add(ident, kind, title, summary, body="", status="active", links=(), **extra):
        value = dict(id=ident, kind=kind, title=title, summary=summary, body=body, status=status,
                     links=[{"rel": rel, "to": to} for rel, to in links], **extra)
        s.put(value, 0, "Initial migration: preserve source context and current user intent")

    sections = [
        (1,13,"Two distinct layers: application and coding work"),(14,31,"Known application defects"),
        (32,123,"Canonical: typed evidence and linked records"),(124,161,"Settled retrofit policy"),
        (162,212,"JD decomposition and fallback"),(213,257,"Select work by responsibilities"),
        (258,293,"Skills taxonomy and hierarchy"),(294,322,"Relevant independent project"),
        (323,358,"Resolved writing inputs"),(359,410,"Item, group, section and document checks"),
        (411,453,"Original layout policy; see later two-page amendment"),(454,485,"Bounded block repairs"),
        (486,574,"Application observability"),(575,629,"Evaluation and calibration"),
        (630,702,"Earlier coding controls; model roles later superseded"),(703,744,"Narrow Jev questions"),
        (745,768,"Evidence versus worker self-approval"),(769,796,"User feedback and diagnosis"),
        (797,826,"Usage controls"),(827,848,"Former implementation sequence"),
        (849,875,"Required runtime deliverables"),(876,903,"User feedback on the twenty points"),
        (904,928,"User amendment: one OR two pages"),(929,1034,"Block ownership versus number of initial writer calls"),
        (1035,1126,"Observability component choices"),(1127,1182,"One coherent change per commit"),
        (1183,1199,"Snapshots, versions and replay"),(1200,1222,"Human participation in ordinary language"),
        (1223,1238,"Reusable anchor discussion, now project-specific")]
    s.import_source("Agreed discussion - verbatim notes - 2026-09-22.txt", "source-agreement", snapshot=True, ranges=sections)
    sources = [
        ("RECOVERY-PLAN.md","source-recovery","historical"),
        ("HARNESS-V3-DESIGN.md","source-v3-design","historical"),
        ("HARNESS-V3-PLAN.md","source-v3-plan","historical"),
        ("CODING-CONTROLS.md","source-old-controls","historical"),
        ("CONTROL-TEST-RESULTS.md","source-old-results","historical"),
        ("NOW.md","source-old-now","historical"),
        ("MEMORY.md","source-old-memory","historical"),
        ("PROGRESS-TRACKER.csv","source-old-tracker","historical"),
        ("USER-WORKFLOW.md","source-user-workflow","reference"),
        ("00-APPLICATION-ENGINE.md","source-engine","reference"),
        ("01-CANONICAL.md","source-canonical","reference"),
        ("project-memory/sources/latest-user-request-2026-09-23.txt","source-current-request","reference")]
    for path, ident, status in sources:
        s.import_source(path, ident, status, snapshot=True)

    add("rule-scope", "rule", "Current authorization and model independence",
        "Current work is this project's memory harness. Resume application repairs only after orienting Lohith and agreeing the next task. No fixed model, no required Sol/Astra switch; no paid run, submission, deployment or push in this setup.",
        links=[("based_on","source-current-request")])
    add("rule-collaboration", "rule", "Lohith steers and judges outcomes",
        "Assume Lohith returns with no context. State goal, current checkpoint and next action briefly. Save feedback and decisions immediately; show concrete results for his judgment. Do not turn questions into changes or technical success into acceptance.",
        "Keep progress updates short and regular. Explain any verification by its input, expected behavior, observed result and limitation. The user need not memorize commands or maintain records manually. If either partner drifts, show the connection to the project and agree whether to change course.", links=[("based_on","source-agreement-028")])
    add("rule-memory", "rule", "External memory is the durable working state",
        "Load the overview and current checkpoint, then fetch linked detail. Record standalone what/why/scope/source/status; no chat-dependent shorthand. Save significant changes before continuing or clearing. Historical sources are evidence, not active instructions.",
        "The record graph is versioned JSON; SQLite is a rebuildable search index. Use expected_revision to reject stale writes. Do not edit prior revisions. Exact agreement snapshots and old plans remain retrievable. Latest user instructions override older records; save that override instead of silently obeying stale state.")
    add("rule-changes", "rule", "Handle cross-checkpoint changes without losing the route",
        "For a significant change, record the request and paused position, inspect known dependencies and code, explain affected checkpoints to Lohith, then implement the agreed scope. Preserve earlier versions; reopen only affected work. Commit one coherent change with a meaningful task label.",
        "A dependency query finds recorded links only; it is not a semantic oracle. Commit with explicit file paths and inspect staged diff; never include unrelated dirty changes, .env, raw logs or generated resumes. A technical completion uses review status; accepted requires the actual user statement and source. That record is provenance, not cryptographic proof of human identity.", links=[("based_on","source-agreement-026")])
    add("rule-application", "rule", "Settled application requirements",
        "Tailor strong, readable resumes to JD work; tool retrofit is authorized. Preserve employers/dates. All four employers, max four bullets each, no eight-total cap; relevant independent project; one or two pages without deleting useful content to force one. Jev decides/checks; writers create.",
        "Canonical tool inventory is intentionally incomplete. Do not ask for exhaustive freelance/tool lists or reopen employer-specific tool verification. Do not invent companies, dates, metrics or repository URLs. No minimum-word evaluation loops. Skills separate concrete tools from methods/domains. Child checks precede parent checks. One initial writer request with separately owned blocks was recommended in the follow-up, not independently proven superior. Original JD, resolved source text and explicit options must reach each decision/writing unit.",
        links=[("based_on","source-agreement-004"),("based_on","source-agreement-023"),("based_on","source-agreement-024")])
    add("rule-observations", "rule", "What automatic observations do and do not capture",
        "Record tool lifecycle metadata locally when trusted Codex hooks deliver it. Save semantic decisions via the memory CLI; hooks do not understand conversations. Check health each fresh session. Never claim configured hooks are active without live evidence.",
        "Raw prompts, command bodies, credentials and tool outputs are not copied into hook events. Tool IDs, timing, explicit exit codes and transcript pointers support investigation. Hosted web tools may be uncovered. This is observation and continuity, not a security sandbox. Local event logs are not Git history; record important outcomes in versioned records and focused commits.")

    modules = [
        ("module-canonical","Canonical evidence","Typed records for employers, work, facts, metrics, restrictions, tools and project patterns. Resolve IDs to their actual contents.",["source-agreement-003","source-canonical"]),
        ("module-jd","JD interpretation","Preserve original passages; decompose requirements with narrow options. Do not let repeated extraction failure prevent all writing.",["source-agreement-005"]),
        ("module-selection","Work selection","Fit is based on work responsibilities and scope; tool retrofit is allowed. Avoid mechanical recency and bullet quotas.",["source-agreement-006","source-agreement-004"]),
        ("module-skills","Skills","Categorize actual tools and methods correctly. Check each skill, group and whole section in order.",["source-agreement-007"]),
        ("module-project","Independent project","Include a JD-relevant local project using the user's established small-scale-before-company-work pattern. No exhaustive project inventory required.",["source-agreement-008"]),
        ("module-writing","Writing blocks","Each block owns its instructions, resolved evidence and revision history. Follow-up recommends coordinated initial drafting then bounded block repairs; separate initial calls are not settled.",["source-agreement-009","source-agreement-024"]),
        ("module-checks","Jev and deterministic checks","Python checks structure; Jev asks narrow semantic questions using complete inputs. Item results feed group then section then document checks.",["source-agreement-010","source-agreement-016"]),
        ("module-rendering","Rendering and visible coverage","One or two pages. Calculate coverage from final visible content. Do not shorten the letter to fix resume overflow. Preserve renderer/public JSON where possible.",["source-agreement-011","source-agreement-023"]),
        ("module-repairs","Bounded repairs","Target the failed block with its evidence and neighbors; reject edits to other IDs; recheck affected dependencies; at most two shared repair rounds in saved proposal.",["source-agreement-012","source-agreement-024"]),
        ("module-observability","Application run visibility","Observe stage/request start/end, retry/timeout/failure, saved intermediate results, latency and cost. This application layer is distinct from coding-session observations.",["source-agreement-013","source-agreement-025"]),
        ("module-evaluation","Evaluate against user-visible examples","Use saved examples and inspect actual output; passing self-written checks is not proof of resume quality. User feedback must point to the changed behavior.",["source-agreement-014","source-agreement-017","source-agreement-018"])]
    for ident, title, summary, refs in modules:
        deps = [("based_on", ref) for ref in refs] + [("uses", "rule-application")]
        if ident != "module-canonical":
            deps.append(("depends_on", "module-canonical"))
        add(ident,"module",title,summary,status="reference",links=deps)

    add("state-existing-code", "evidence", "What exists versus what is proven",
        "Application CLI, canonical.yaml, renderer and v3 implementation exist. Current resumes have not met Lohith's standard. Old control tests/real worker proof and application visibility were pending; do not restart the old worker merely to inspect state.",
        "Inventory on 2026-09-23: pre-existing uncommitted harness/skills.py, tests/test_skills_v3.py, pyproject.toml and devcontrol work must be preserved. devcontrol process_alive uses os.kill(pid,0), unsafe on Windows; STOP handling during verification needs review. Last prior application commit e58cace. Historical Stibo run jobs/stibo-jd-20260920T202846388022Z/run.json says STOPPED, 28 HTTP attempts, reported USD 0.032269598. No fresh application run was performed during memory setup. No assumption that original implementation is usable until inspected.",
        links=[("based_on","source-old-results"),("based_on","source-old-tracker"),("based_on","source-old-now")])
    add("decision-superseded", "decision", "Retired instructions and preserved distinctions",
        "Retire model locks, old active steps1–3 authorization, one-page-only rules and missing-OpenRouter-approval claims. The source agreement remains preserved; later user amendments win.",
        "User chose a project-specific memory setup now, not a universal framework or Beads installation. Earlier restriction against databases belonged to the application design, not this newly requested coding-memory index. Existing OpenRouter permission persists, but setup scope does not request a paid run. Old documents can contain contradictory complete/pending states; inspect evidence. Do not infer independent initial model calls from separately owned writing blocks.",
        links=[("supersedes","source-old-now"),("supersedes","source-old-memory"),("based_on","source-current-request")])

    add("checkpoint-0","checkpoint","Agree what the application must produce",
        "The detailed twenty-point discussion and later amendments are preserved. The application output is not yet accepted.",status="accepted",
        links=[("based_on","source-agreement")], acceptance={"user_statement":"20. all good", "source":"source-agreement-022; subject to later explicit amendments"})
    add("checkpoint-memory","checkpoint","Prepare this project for a fresh chat",
        "Building linked memory, selective retrieval, startup instructions and local observations. Application repairs remain paused.",status="in_progress",
        body="Finish setup, show the restart briefing and explain observation activation. Then Lohith reviews this foundation before choosing the next application task. Do not treat previous steps1–3 instructions or a model name as current authorization.",
        next_action="Finish memory setup and present a short fresh-chat handoff to Lohith.",
        links=[("based_on","source-current-request"),("uses","state-existing-code"),("uses","decision-superseded")])
    checkpoints = [
        ("checkpoint-1","Control the coding work","Existing devcontrol code needs inspection; its final proof is pending. Current memory setup supplies continuity and observation, not proof of all old worker controls.","planned",["state-existing-code"]),
        ("checkpoint-2","Demonstrate one small coding task","Show an actual bounded change, its evidence and history before trusting the coding workflow.","",["checkpoint-1"]),
        ("checkpoint-3","See inside an application run","Make stage, request, time, saved output and failure visible. This is application instrumentation, not the coding hooks.","",["module-observability"]),
        ("checkpoint-4","Improve the resume builder","Repair resolved evidence, selection, skills, projects, writing, hierarchy and final layout according to the agreement.","",["module-canonical","module-jd","module-selection","module-skills","module-project","module-writing","module-checks","module-rendering","module-repairs"]),
        ("checkpoint-5","Inspect saved data and rendered examples","Replay locally and inspect visible output before spending on a full external run.","",["checkpoint-4","module-evaluation"]),
        ("checkpoint-6","Run one actual JD end to end","Produce resume PDF, letter PDF, JSON, portable context and an inspectable report; Lohith judges the result.","",["checkpoint-3","checkpoint-5"]),
        ("checkpoint-7","Check a different JD","Confirm tailoring beyond the first example after the first output is inspectable.","",["checkpoint-6"]),
        ("checkpoint-8","Use the application routinely","One understandable JD-to-files workflow with a clear output location and bounded failures.","",["checkpoint-7"])]
    for ident,title,summary,status,refs in checkpoints:
        add(ident,"checkpoint",title,summary,status=status,links=[("depends_on", x) for x in refs],next_action="Discuss the bounded task with Lohith when this checkpoint becomes current.")

    add("project", "project", "Local job-application builder",
        "Paste a JD and receive a readable tailored resume PDF, cover-letter PDF, application JSON and reusable chat context.",
        "Two layers: this coding-memory harness helps Lohith and an agent build the separate application pipeline. Preserve existing agreements; avoid universal-framework work. The full source-agreement is the detailed plan; modules and checkpoints route to exact sections. Fresh sessions must explain current position, then follow Lohith's steering.",
        links=[("rule", x) for x in ("rule-scope","rule-collaboration","rule-memory","rule-changes","rule-application","rule-observations")] + [("plan","source-agreement"),("decision","decision-superseded")],
        focus="checkpoint-memory", checkpoints=["checkpoint-0","checkpoint-memory"]+[f"checkpoint-{i}" for i in range(1,9)])
    s.rebuild()
    print(s.doctor())
    print(dashboard(s))


if __name__ == "__main__":
    seed()
