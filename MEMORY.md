# Project memory index

- `NOW.md`: current implementation and first-run resume state.
- `README.md`: actual CLI commands, setup and current limitations.
- `FIRST-RUN.md`: Stibo output, measured cost, failed writing checks and next improvements.
- `WRITING-V2-DESIGN.md` and `WRITING-V2-PLAN.md`: Astra's writing/repair decisions and bounded Sol implementation handoff.
- `WRITING-V2-RESULTS.md`: fresh Stibo/McKesson harness-versus-one-shot costs, statuses, remaining failures and blind-review method.
- `HARNESS-V3-DESIGN.md` and `HARNESS-V3-PLAN.md`: current Astra architecture and seven-task inline Sol handoff. Supersede conflicting earlier designs. Design complete; implementation pending model switch.
- `USER-WORKFLOW.md`: concrete proposed terminal experience, question/answer/resume behavior, writing-quality requirements, supplied JD references and actual renderer findings.
- `ARCHITECTURE-REVIEW.md`: unapproved critique, source findings, conceptual architecture, state/schema proposals, API sources and evaluation approach.
- `00-APPLICATION-ENGINE.md`: existing application rules and fixed external JSON contract; do not silently replace it.
- `01-CANONICAL.md`: authoritative candidate evidence, including nuanced restrictions and user-authorized universal stack retrofit. Retrofit is settled by the user and must not be reopened or gated on employer-specific tool records.

Durable user preferences: smallest understandable system; runtime independent of coding agents and ChatGPT; preserve renderer/public JSON where possible; bounded local repair, resumability and auditable provenance; render manual JSON edits with zero API calls; handoff later conversations to ordinary ChatGPT; no arbitrary confidence thresholds. User initially wanted design first, then explicitly authorized implementation and one real run. Do not ask for implementation permission again.

Latest binding clarification: prioritize tailoring the resume/cover letter to the JD. Fit depends on actual work, not tool matches. The technology inventory is deliberately incomplete; never ask for exhaustive tool/freelance enumeration. Use Jev for semantic decisions and validation with well-designed state/options; generative models create only. Do not propose generative validators or diagnostic judges. Normal runtime requires no routine human approvals. Explain things plainly, avoid abstract terminology, and ask for needed inputs as a short concrete list.

Readability is as important to the user as ATS compatibility. They report many applications with unreadable AI text and no calls; there is no good prior resume/letter to request as a benchmark. Establish clear writing examples during development. Explain product interactions with actual screens/commands, not only architecture diagrams.

Renderer and structural example live at `C:\Users\91910\Downloads\resume-builder\build.py` and `app.json`. Old generated content and hardcoded renderer contacts are not canonical evidence. Six JD examples are supplied; see USER-WORKFLOW.md. Do not ask the user to resend these inputs.

Keep bulk detail in files. Do not re-read large source files for unrelated follow-ups; read relevant source sections when a decision needs them. Use a subagent for broad repository/search exploration as requested by the session protocol.

Model/cost preference: user wants Astra for material architectural choices, then an immediate stop to switch to Sol for implementation, tests, routine fixes and experiments. Do not spend Astra turns executing an already specified plan. Sol should raise genuinely new structural choices with a concrete explanation; do not request model switches for ordinary coding judgments.

Writing v2 result: both fresh live jobs are `REVIEW_REQUIRED`, despite clean one-page PDFs and passing global consistency/readability/coverage checks. Stibo used 44 attempts/$0.044793662; McKesson 43/$0.044369466. Both exhausted two repairs with abstract-language failures; McKesson also retained opening/proof repetition. One-shot controls cost $0.01258445 and $0.01170511. Do not claim the harness is better until the user completes the blind A/B review. Further changes to the writing/repair architecture are a material design decision suitable for Astra after that review.

New binding correction after output review: the current no-project instructions in `00-APPLICATION-ENGINE.md` and `01-CANONICAL.md` no longer represent the user's intent. Every tailored resume should normally include one directly relevant independent project, retrofitted to the JD from the user's confirmed working pattern: build a small local version before the larger company implementation and publish it on GitHub. The user does not want an exhaustive project inventory in the canonical. Do not run another paid application until Astra redesigns how this authorized project pattern is represented without inventing metrics, dates, repository URLs or business outcomes.

The user rejects half-empty resumes, one-line summaries, a one-line flat skills dump and mechanical 4/1/2/1 employer allocations. A finished resume should use the page well; give relevant older roles enough evidence; include meaningful summary, categorized skills, experience and a project; and allocate space by the JD rather than recency. Skills must separate actual types such as languages, frameworks/libraries, models/providers, cloud/platforms, data/storage, automation/orchestration, deployment/DevOps and methods. Broad domains such as AI, automation, MLOps, RAG and prompt engineering must not be mislabeled as technologies or left as unexplained placeholders. Exact JD terms still require complete coverage, but the display must be readable and technically coherent.

Communication correction: do not silently perform long harness work and return only artifacts. Before or with results, show a compact visual workflow, what each stage/gate does, what passed, what failed, costs, and what the output does and does not prove. The user prefers short sections, diagrams, tables and direct wording suitable for quick ADHD-friendly scanning.

Latest user clarification: the one-page/short bullets/no unnecessary repetition rules STILL apply. Remove the eight-total experience limit; use maximum four per employer with no mandatory quota. Do not remedy thin writing by adding a minimum-length evaluator or more loops. Build substantive first drafts from structured YAML and a complete brief. Deep Jev means per skill -> per group -> Skills; per bullet -> employer -> Experience; then application. Separate logical decisions can share batched HTTP calls. Whole-section PASS cannot replace child checks. New writing ranges are guidance only; retain one initial attempt plus two shared repair rounds.

V3 handoff records the actual causes and changes with schema contracts, file-level tasks and regression cases. Do not claim all implementation ambiguities or model mistakes are impossible. The user's structural critique supersedes the request for blind A/B choices. Source files have not yet been migrated; v3 Task 1 archives original Markdown, creates populated canonical.yaml and reconciles the new project policy before paid generation.
