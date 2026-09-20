# What using the harness would look like

Discussion proposal, 2026-09-19. These commands/screens describe the intended product; they are not implemented commands.

## The thing you open

A local program, run from PowerShell or Windows Terminal. You type `apply-job`. This opens a guided application-generation process inside that terminal. It is not a new chat agent, and no ChatGPT/Codex conversation is needed to run it.

For the first version, recommend a CLI rather than adding a web UI before the generation process works. A graphical interface could use the same saved job state later; it is not necessary for the requested workflow.

## One-time setup

The program is configured with the canonical/engine paths, renderer, OpenRouter credentials and chosen models. Missing fixed header details are collected once. Setup checks that the renderer can accept a known JSON and produce both PDFs. Credentials stay local and out of Git.

Normal jobs reuse these settings. No repeated questions about tools or employer-level technology history.

## Starting an application

Example proposed screen:

```text
PS> apply-job

Paste the job description below.
When finished, type /done on a new line.

[paste JD]
/done

Saved job: stibo-ai-solutions-engineer-001
Reading job requirements...
Choosing the strongest work examples...
Writing your resume...
Checking clarity and repairing weak wording...
Writing your cover letter...
Building and checking PDFs...
```

A typed completion marker avoids relying on Unix-only terminal instructions. File input should also work: `apply-job new --jd "C:\path\job.txt"`. A malformed or empty paste produces a plain input error before spending tokens.

Progress messages are generated from program state. They are not a model narrating its thoughts. The user can leave it running; ordinary generation does not require approving each decision or bullet.

## What happens behind that screen

1. Save the JD and the exact source/config versions for this job.
2. Create structured JD data. Jev judges priorities, categories and whether the draft extraction represents the JD; code checks source references. Any generative extraction call creates a draft only, not an approved interpretation.
3. Give Jev specific requirements and candidate work examples. Use its bounded judgments and code rules to select and allocate evidence. Tools come from the JD under the settled retrofit policy.
4. Supply the writer with the chosen work, permitted results, required terminology and length targets for each block. Generate bounded groups for each employer, then summary and cover letter.
5. Jev checks whether the writing clearly demonstrates the assigned work and is understandable; code checks exact constraints. If a bullet is vague or overloaded, send that bullet back with the specific failed check. Accepted bullets stay unchanged unless their dependencies change.
6. Feed accepted text into the existing JSON contract and renderer. Check the actual PDFs for page count, missing/clipped text and readable layout. Produce the handoff from the final saved version.

The writer creates. Jev makes semantic decisions and validates. Code runs the process. This is still a proposal to test, not a claim that readability can already be guaranteed by Jev.

## Exactly where a question appears

If essential information cannot be filled from setup/source facts and cannot safely be omitted, the program stops at a normal terminal input prompt. Example of a missing personal detail, not a tool question:

```text
One detail is missing for this Netherlands application:
What correspondence address should appear on your resume?

Type the address, or type /later to save and exit.
> [your answer]

Answer saved. Continuing...
```

The answer is typed after `>` in the same terminal. The program saves it to this job's local state. It is not necessary to open a second chat, edit an internal JSON, or contact a development agent.

If the user types `/later`, work stays saved. `apply-job resume <job-id>` reopens the pending question and then continues. If the terminal closes unexpectedly, resume reconstructs the same pending state. Noninteractive file/pipeline runs must save pending questions and exit with a clear needs-input status, rather than hanging where no one can answer.

The default scope of an answer is the current job. Saving a new personal fact for all future applications must be explicit; one answer must not silently rewrite the complete canonical. Fixed personal details should normally be resolved during setup, making this runtime path uncommon.

Questions are not used to ask whether the user knows a JD tool, approve bullets, or compensate for a confused classifier. Missing optional details can be omitted. Model uncertainty triggers bounded repair/review status, not repeated demands that the user supervise the program.

If the program cannot finish within its limits, it saves the draft and explains the actual problem. It must not print success or return a silently weakened application. The user can inspect/resume it later; this exceptional failure is distinct from an ordinary fact question.

## The result

```text
Created:
  resume.pdf
  cover_letter.pdf
  application.json
  chat_context.md

Saved under: jobs/stibo-ai-solutions-engineer-001/

Open the PDFs to review the application.
```

The folder also holds the original JD and run/decision records. These records are available through `apply-job inspect <job-id>` but need not clutter normal output. The harness generates applications; it does not submit them automatically.

The user can read the PDFs, edit application.json manually or through an ordinary ChatGPT conversation, and run `apply-job render <job-id>`. This rebuilds PDFs and the handoff without API calls. Edited text is marked as changed since model QA, while the prior accepted version remains available.

`chat_context.md` is uploaded to the user's ordinary ChatGPT conversation for forms, recruiter questions and interview preparation. That chat is outside the harness.

## What readable means for this project

The user's stated failure is mass-produced resumes containing unreadable AI prose. ATS terminology and readability are both core requirements. A long list of matched keywords is not sufficient.

Initial writing standards:

- A recruiter can tell what was built and what changed after one reading.
- Each bullet has one main point with concrete actions and a supported result or operational consequence.
- Technology names explain how work was done instead of replacing the explanation.
- Summary states a clear professional identity; the cover letter gives a specific reason and example rather than repeating the entire resume.
- No vague claims of transformation, piles of abstract technical nouns, or repetitive sentences that differ only in tool names.

For example, the canonical's approval dashboard can be described plainly: "Cut approval-to-publication time from days to under 60 seconds by letting clients review, edit and publish through a self-service dashboard." This is an illustrative wording example, not a completed JD-tailored bullet.

Use Jev questions that isolate first-read clarity, a visible action/result, relevance to the assigned requirement and avoidable repetition. Test them against user-reviewed pairs of readable and unreadable writing. A label from an untested classifier is not enough to establish writing quality.

There is no need for the user to supply a good prior resume. During development, create a small set of alternative bullets from the same facts and agree on which are clear and persuasive. That becomes the writing benchmark used to tune the harness, not a recurring approval step during every application.

## Inputs now available

Renderer: `C:\Users\91910\Downloads\resume-builder\build.py`.

Example JSON: `C:\Users\91910\Downloads\resume-builder\app.json`. This is a renderer compatibility example, not a factual source or a good-writing benchmark.

Six JDs were supplied:

| JD | Source | Useful test focus |
|---|---|---|
| Royal Canin — AI & Automation Lead | Attached file fa06253a-6900-4cc8-a46a-0e4a9bd90496 | Internal automation, testing, measurable value, reusable assets |
| Stibo Systems — AI Solutions Engineer | Attached file c90f281b-b5f7-403f-b610-df1807363156 | Business processes, practical AI, adoption and value |
| McKesson — Technical AI Enablement Senior Engineer | Attached file b720d64d-e322-42e8-898d-816715fad87c | Integrating pilots into production systems |
| Siemens Energy — AI Implementation Specialist | Pasted directly in conversation | Practical solutions, stakeholder work, adoption |
| AI Application Engineer — company not supplied | Pasted directly in conversation | Stateful agent applications, RAG, production reliability |
| KeyShot — backend/web engineering role, exact title not supplied | Pasted directly in conversation | AI-assisted software development, TypeScript/AWS backend quality |

Attached files are under `C:\Users\91910\.codex\attachments\<attachment-id>\Pasted text.txt`. Preserve the exact pasted JDs when turning these references into regression fixtures; the test-focus descriptions above are not substitutes for the original text. Do not infer missing employer names or job titles.

These six are enough for initial design/prototype cases. No API key is needed to explain the workflow or inspect the renderer. A local key will be needed when actual API experiments are authorized.

## Renderer inspection findings

Read-only inspection found two files, build.py and app.json. The current renderer runs as `python build.py <application-json> <output-directory>` and uses ReportLab. Its resume and cover-letter input structure matches the existing engine contract; it is worth adapting rather than replacing. The example JSON is for Rydoo.

Changes needed before integration:

- Header values are hardcoded in both document functions, including a Heilbronn address that differs from the current canonical. Use canonical-driven local header data; do not adopt old renderer values as confirmed facts.
- Resume body/bullet text is 8.5 pt. There is no enforced maximum page count, clipping/text audit or overflow report. Establish a readable layout and adjust content to it.
- Input is not schema-validated, and ordinary strings are passed into ReportLab markup without a safe escaping boundary.
- Output filenames use company alone, risking collisions. Use a unique job/revision directory and safe filenames.
- Resume is written before the letter; a letter failure can leave partial output. Stage both and report completion only for a complete checked set.
- No dependency manifest or tests are present. Record dependencies and verify a known render when implementation is authorized.

No renderer files were edited and no PDF build was run in this review.
