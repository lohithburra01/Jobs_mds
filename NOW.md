# Resume state - 20 September 2026

## Current task

The user reviewed the output and rejected the current resume structure. Do not run another paid job. First explain the existing harness and postmortem clearly. Then stop for the requested Astra switch before making structural design decisions. Read the newest corrections in `MEMORY.md`: full-page use, richer balanced evidence, categorized skills and one JD-specific retrofitted independent project are now required. The old no-project rules in the engine/canonical are stale relative to the user's direct instruction.

User wants paste JD -> tailored resume and cover letter. Fit is based on work. Target technology retrofit is settled and mandatory; never ask for employer-specific tool history or an exhaustive technology list. Jev makes semantic decisions/checks, the writer creates prose, and the normal CLI is independent of Codex.

## Implemented

Writing v2 includes single-purpose writing blocks, evidence-specificity decisions, a reserved cover-letter proof, whole-document local/relationship/requirement/global assessment, deterministic block repair, persistent three-attempt budgets, writing-version isolation and one-call controls from identical prepared inputs. Public Application JSON and the renderer contract remain unchanged.

The oversized Jev request found during the first Stibo v2 attempt was fixed by deduplicating shared state, limiting batches and caching cases independently. A later accounting regression fix persists a stage baseline before calls so resumed work keeps pre-interruption cost attribution. Existing Stibo stage rows remain historically incomplete; its total counters are correct.

## Live results

Stibo v2: `jobs/stibo-jd-20260920T151708861102Z`, `REVIEW_REQUIRED`, 44 attempts, $0.044793662, two repairs. Remaining: abstract summary, opening, closing and Think Round bullet. One-shot: one call, $0.01258445.

McKesson v2: `jobs/mckesson-jd-20260920T152242318211Z`, `REVIEW_REQUIRED`, 43 attempts, $0.044369466, two repairs. Remaining: abstract summary/opening/closing/Think Round/Cognizant language, wrong closing job and opening/proof repetition. One-shot: one call, $0.01170511.

All eight final comparison PDFs are one page, selectable, at least 10 pt and visually inspected without clipping, overlap, missing glyphs or unreadable text. Blind packages are inside each job's `comparisons/blind-review/`; mappings are separate one directory above.

## Next action

Give the user an ADHD-friendly visual explanation of every stage and gate, distinguish backend safeguards from actual resume quality, and state the root causes in the implementation. The blind review is superseded by the user's structural critique. After the explanation, the next work is a material redesign; the user previously required an immediate stop so they can switch from Sol to Astra for that decision.

## Operational notes

Bundled Python: `C:\Users\91910\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

`.env` works and must never be displayed or committed. Jobs and temporary renders are ignored. No application submission, deployment or Git push is authorized. Local branch `harness-prototype` has no commit yet because `.git` is outside the writable sandbox; retry normal approval only after verification if useful.
