# Project startup and working memory

This repository builds Lohith's local JD-to-resume/cover-letter application.
The separate project memory harness helps the human and coding agent build it.

At every fresh session, before product changes:
1. Read NOW.md and MEMORY.md (short pointers, not the project history).
2. Run `powershell -NoProfile -File scripts/project-memory.ps1 start`.
3. Run the same launcher with `health`; configured hooks are not proof they run.
4. Read `show` for the current checkpoint and its relevant linked records. Use
   `source SOURCE-SECTION-ID` for exact agreement text. Do not load all archives.
5. Tell Lohith the goal, current position, what remains, and the next concrete action.

Use the latest explicit user instruction. Save changed intent in the memory graph.
Old Sol/Astra requirements and old active-task notes are historical, not binding.
Any capable agent can use this CLI. Do not launch another model just to resume.

During work:
- One bounded task at a time. Save its scope and paused position in the current record.
- Record decisions, feedback, discoveries and changed status as they happen, before
  dependent work. Use `put --file PATH --expected-revision N --reason TEXT`.
  Write input JSON in project-memory/scratch; it is excluded from Git.
- Keep records understandable without chat: what, why, scope, source, next action.
- For significant design changes, save a change record; inspect `impact ID` plus
  actual code; explain affected checkpoints to Lohith before expanding the work.
  Preserve the earlier revision and say which active rule or module contract changes.
  A new fact inside a module does not automatically change that module's contract.
- Use `event` for meaningful operational notes. Hooks save tool metadata when active;
  they do not automatically save the meaning of conversations. No raw secrets in logs.
- Show real results and limitations. Use status `review` when implementation is ready.
  Only use `accepted` after Lohith accepts; record his statement and source.
- Commit one coherent change, with an ID and meaningful explanation, after reviewing
  the explicit staged files. Preserve all unrelated dirty work. Never `git add .`.
- End by saving current status/next action, refreshing `view`, and explaining the result.
  Keep NOW.md/MEMORY.md as pointers; do not append session narratives to them.

Details and examples: project-memory/OPERATING-GUIDE.txt. No paid application run,
submission, deployment or push is implied by the memory setup task.
