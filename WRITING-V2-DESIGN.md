# Writing v2: decisions for the next implementation

20 September 2026. Astra design pass requested by the user; implementation belongs to Sol after the user switches models. This document supersedes the writing/repair parts of PROTOTYPE-PLAN.md. It does not change the canonical, public application JSON, retrofit authority or provider choices.

## What the first run actually revealed

1. In the saved Stibo plan, Corominas bullet 1 owns seven of eight requirements. Six other bullets receive only “Show a clear, relevant professional result.” A 32-word bullet cannot express seven hiring criteria well.
2. All three letter paragraphs receive the same pool of evidence. Their purposes differ in prose, but no example is reserved for the middle paragraph. The opening and middle both retell the 200-client pipeline.
3. Generation.realize exhausts local repairs before the full application is checked. Global readability failure therefore arrives after some blocks have spent all their attempts.
4. Repairs receive the failed rubric again, without a specific operation. The three closing drafts mostly rearrange the same vague promises.
5. A repair batch contains only failed blocks. Passing neighboring paragraphs disappear from the writer/checker's view, making cross-paragraph repetition harder to resolve.
6. The prototype hard cap of 32 words contradicts the engine's explicit allowance of up to 38 when needed. Word count alone does not establish poor writing.
7. Cognizant's selected source is a general data-quality paragraph. The canonical also contains production scale and latency outcomes. The selection rule never explicitly compares how concrete two similarly relevant examples are.

These are reasons to improve planning and feedback before buying a stronger writer or allowing more retries.

## Chosen approach and alternatives

Choose fixed writing roles, specific Jev issue choices, and one bounded repair loop over the complete draft. This keeps the writer's job limited to creation and makes corrections actionable.

Prompt-only changes would reduce repetition but leave global failures disconnected from repairs. An open-ended critic producing rewrite advice would add another generative decision-maker and an uncontrolled loop. Neither is the next implementation.

## 1. Give each block one job

Keep the current eight-bullet allocation and employer minimums for this experiment. Do not redesign all evidence selection at once.

Add one Jev choice per evidence unit to the existing coverage batches: CONCRETE_OUTCOME (a specific recorded result, scale or operational consequence), CONCRETE_WORK (a specific implemented artifact/action but no recorded consequence), GENERAL (broad capability description), UNCERTAIN. This is source specificity, not a requirement for numeric metrics. Scores are deterministic tie-breaks, not calibrated probabilities.

Existing relevance and marginal-coverage scores stay primary. Within equal relevance/coverage rank, prefer CONCRETE_OUTCOME, then CONCRETE_WORK, then GENERAL/UNCERTAIN, before source ID. Never transfer a metric from an unselected unit into a selected one. If the general Cognizant unit still wins, show that result in the experiment; do not special-case an employer to force a metric.

Separate coverage bookkeeping from writing purpose. A source may support many requirements, but its bullet gets exactly one primary requirement. Assign CORE requirements first, then SUPPORTING, in stable JD order. For each requirement choose an unassigned selected source by support strength, source specificity and stable ID, provided support is at least ADJACENT. If all supporting sources already have a primary requirement, record this requirement as secondary coverage potential; do not concatenate it into an existing purpose. Afterward give every unassigned bullet its strongest supported requirement, allowing reused requirements. If none is supported, its purpose is the concrete work named by its own source heading. This never turns absence of work coverage into a tool-gap rejection.

Store primary_requirement_id and potential_requirement_ids separately. The final text audit determines actual coverage; the assignment itself is not proof. Each bullet is an outcome/operational change plus owned action and only the technical detail needed to understand it. JD terms remain freely retrofittable where they perform a function. Existing target_terms are relevant choices, not a requirement to pack three names into every bullet.

## 2. Give the letter three different jobs

Choose the proof example deterministically from selected sources: strongest summed CORE work support, then source specificity, then stable ID. Save its ID in the writing plan before generation.

| Block | Job | Permitted evidence | Target / hard maximum |
|---|---|---|---|
| Summary | Professional identity, problems solved and central stack | Canonical identity and selected work; no detailed achievements | 35–50 / 60 words |
| Letter opening | Identify the role and connect one stated hiring need to the candidate's experience | JD plus identity/capability context; no named-employer case study or metrics | 35–50 / 60 words |
| Letter proof | Explain one concrete example and why it matters | Only the reserved source, its inherited boundaries and assigned target terms | 55–80 / 95 words |
| Letter closing | State one practical contribution to a JD need and close naturally | JD plus supported capabilities; prospective wording; no second case study or repeated metrics | 25–45 / 60 words |

These letter limits are initial product defaults, not externally validated measures of quality. Being shorter than the target range is not a failure when the paragraph does its job. The existing three-paragraph JSON stays intact.

Useful closing direction for Stibo: connect the candidate's experience to taking a manual workflow through implementation and testing it with the people who use it. Do not promise adoption figures or invent a company problem absent from the JD. A polite final sentence is allowed; enthusiasm alone is not the paragraph's contribution.

## 3. Check the complete draft before spending repair attempts

The control flow is: draft every block once → assess current blocks and their relationships → rewrite only identified blocks → reassess affected checks. At most two repair rounds follow the initial draft. Do not run the current complete local repair loop for each employer before the document check.

Continue batching initial resume generation by employer; write the three planned letter paragraphs together. For each repair, supply:

- Only selected IDs as writable blocks, with their own source evidence.
- The complete current resume and letter as read-only context, labeled as generated text rather than factual evidence.
- Specific issue codes, affected IDs, and fixed repair instructions.
- Neighbor text to preserve, previous text, target and maximum length.

The writer must return exactly the writable IDs. It must not borrow a fact from a neighboring block. Existing immutable identity/chronology/education assembly continues.

## 4. Jev reports specific problems; code selects the repair

Use named PASS/FAIL/UNCERTAIN questions rather than free-form critic prose. Record probabilities, but introduce no numeric confidence threshold. Replace the current omnibus local clarity/purpose checks with these questions where applicable:

| Issue on FAIL | Applicable block | Fixed repair instruction |
|---|---|---|
| UNSUPPORTED_CLAIM | All | Remove or narrow the unsupported claim using only this block's selected source; preserve work/status/metric scope. |
| MULTIPLE_POINTS | All | Keep the assigned primary point; remove independent claims and excess implementation details. |
| NO_CONCRETE_CHANGE | Bullets, proof paragraph | State the source's actual action and specific output/consequence; a concrete artifact is sufficient when no outcome is recorded. |
| ABSTRACT_LANGUAGE | All | Replace broad promises and stacked abstractions with who did what and what changed. Keep necessary technical names. |
| WRONG_PARAGRAPH_JOB | Summary, letter | Rewrite to the exact planned role; show the reserved proof example only in the proof paragraph. |

Each Jev question includes its block ID, purpose and evidence. No issue can fail solely because a retrofitted tool was not recorded for that employer.

Relationship checks run on the completed document: resume bullet pairs (28 for eight bullets), summary versus each bullet (8), and letter paragraph pairs (3). Use choices DISTINCT, REDUNDANT, CONTRADICTORY, UNCERTAIN. Shared vocabulary or use of the same project with a different accomplishment is DISTINCT. A letter may reuse a resume example: do not test resume-versus-letter pairs for repetition. Same-document repetition of detailed accomplishments is REDUNDANT. Cache each check by the two texts, roles and policy, not by unrelated application content. Chunk questions through existing batched_decide; these are batched questions, not 39 separate API calls.

Code chooses the rewrite target: preserve the proof paragraph over letter opening/closing; otherwise preserve the earlier letter paragraph. Preserve experience over summary. For redundant resume bullets preserve the one proving more CORE requirements in the current text audit, then stronger primary support, then earlier resume order; rewrite the other to its own distinct selected work. Do not remove an employer or import another story. If its source cannot supply a distinct point, stop that block for review rather than inventing one.

For contradictions, grounding checks first identify a failed block. If exactly one side fails grounding, repair it. If neither/both can be identified confidently, retain the draft with review status. Do not guess which fact to change. UNCERTAIN is a review result, not a rewrite instruction.

Audit each supported CORE requirement against the current resume using Jev PRESENT/PARTIAL/ABSENT/UNCERTAIN. Supply the allowed support ceiling from the coverage table: an assigned ADJACENT bridge need only communicate that limited contribution. Also return which supplied bullet IDs express it by one binary choice per candidate bullet with positive source support. Record uncertainty explicitly. Missing planned evidence generates MISSING_ASSIGNED_POINT on its primary-owner bullet; if no primary owner or writing it would add an independent point, report a planning gap without automatic reselection. This keeps the next change bounded.

Retain a final whole-application consistency/readability/coverage audit as a backstop. Run it before declaring the current round complete, not after consuming every repair budget. If it fails without a localized issue, save review status; never rewrite the whole document blindly.

## 5. Length and stopping rules

Resume bullet target: 18–32 words. Hard maximum: 38. For 33–38 words ask Jev whether the extra detail is necessary to preserve meaning; UNNECESSARY produces TRIM_DETAIL, NECESSARY passes, UNCERTAIN is review. A count over 38 generates TOO_LONG directly. This restores the original engine rule; it does not grandfather the first draft as acceptable.

TOO_LONG feedback includes actual count, maximum, excess and target. Ask the writer to shorten to the target, not just the boundary. Never truncate text mechanically. PDF overflow remains a real failure even when word limits pass; report it for this slice rather than implementing a new layout optimizer.

One persistent writer-attempt budget per block covers schema failures, local repairs and relationship repairs: initial plus two, total three. No extra global-repair allowance. Persist the attempt reservation before a call, the returned pending draft before checks, and the completed diagnosis before scheduling edits. Interruptions resume the pending phase. A completed valid draft never disappears because its classifier call failed.

If identical failing text returns, or the same block alternates back to an earlier failing text for the same issue set, stop that block. If no mutable block with a diagnosed fix and remaining budget exists, render the draft with REVIEW_REQUIRED. All checks must concern the current text hashes; no stale PASS can approve changed text. Only blocks requiring changes consume a new writer attempt.

## 6. Evaluate writing, not only a green status

Offline tests prove control-flow behavior. They cannot prove recruiter readability or Jev accuracy. Store a small editorial fixture set with expected judgments for: repeated letter story, allowed resume-to-letter reuse, distinct achievements in one project, jargon hiding an action, specific useful technical detail, generic closing versus concrete prospective contribution, justified 35-word bullet, unsupported result. These are developer-authored examples, not calibrated ground truth or a general accuracy score.

After offline tests, run Stibo once on v2 and render its output. Compare with the untouched first run. Then use the supplied McKesson JD as a second case so changes cannot succeed only by recognizing Stibo. Do not tune repeatedly against those two outputs in the same experiment.

For each case, produce one additional same-model, one-call application from the exact same prepared JD/evidence/writing plan and public schema, using the same renderer. It has no repair feedback. The writer still only creates from the fixed brief. Label this “one-shot from the same brief”; it is not equivalent to unrestricted ChatGPT with different context. Report planning cost, writing cost, repair cost, requests and wall time separately. A failed one-shot schema is recorded as failed, not silently repaired.

Show paired outputs without a preferred label first, with a separate mapping file. Human comparison asks: is the main value obvious, does each bullet show understandable work/change, is technical detail relevant, does the letter add a reason to interview, and which version would you send? Allow neither and tie. Jev checks are supporting diagnostics, not the sole judge of its own benefit. Do not claim ATS passing, callback likelihood or general superiority from these cases.

## Version and scope

New runs use writing_version=2 in snapshotted config and versioned policy. Preserve v1 jobs and PDFs. Under v2 code, inspect/render continue working on v1; resume refuses a version mismatch before any state mutation and tells the user to start a new v2 job. This avoids silently overwriting the benchmark or pretending old caches implement new behavior.

Do not add another model, tool-history questions, employer validation, interactive approvals, a new UI, a skill-taxonomy redesign or an automatic submission step. Keep the independent runtime. Structural decisions above are now specified; Sol can implement/test them. If implementation reveals a conflict requiring a different architecture or broader authority, present that specific choice to the user.
