# 00-APPLICATION-ENGINE.md

## Purpose

This file defines the operating rules for evaluating a job description and producing a tailored application. It is an instruction layer, not an evidence store. Do not copy work-history evidence into this file.

The objective is not to make Lohith look generally capable. The objective is to determine whether his visible evidence makes him a competitive candidate for the specific role, then produce a one-page application in which the employer can see the match immediately.

No application engine can guarantee an interview. This engine is designed to remove avoidable rejection risk caused by weak fit decisions, generic evidence selection, tool literalism, unsupported claims, identity drift, and excessive resume density.

## Evidence architecture and source precedence

The active application system has exactly two files:

1. `00-APPLICATION-ENGINE.md` - operating rules, selection logic, output format, and validation.
2. `canonical.yaml` - the sole active factual source for personal details, education, work authorization, employment, the independent-project pattern, metrics, boundaries, and claimable experience.

Apply these rules in order:

1. **The job description defines demand, not evidence.** Use it to identify the employer's buying criteria, terminology, priorities, and constraints. Never treat a JD statement as proof that Lohith has a capability.
2. **`canonical.yaml` is the only active application evidence source.** Use its typed employer systems, facts, metrics, statuses, boundaries, and prototype pattern. Respect every restriction and claim limit.
3. **A direct current-session user confirmation may resolve one narrow missing fact.** Scope it only to the question answered. Add durable corrections to `canonical.yaml` so future applications still use one evidence source.
4. **Model memory, chat summaries, prior resumes, generated bullets, the archived canonical, and old project files are navigation aids only.** They are never factual authority and may not override `canonical.yaml`.

This engine becomes the production application system only when `canonical.yaml` validates and its archive migration report is complete. Do not run applications from an incomplete transitional evidence set.

### Conflict handling

- Within `canonical.yaml`, the most specific employer system, fact, metric, status, boundary, or prototype restriction wins.
- An explicit prohibition, caveat, status, or boundary wins over a sample phrase.
- Do not average, merge, or silently choose between conflicting dates or claims.
- If a conflict changes the fit call or would appear in the application, ask one targeted boundary question. Otherwise omit the disputed detail.
- Absence from a summary is not proof of absence. Search the authoritative evidence before marking a capability unsupported.

## Deprecated evidence

All earlier evidence files are deprecated, including `01-CANONICAL-FACTS.md`, `COROMINAS_CANON.md`, `LOHITH_FULL_WORK_INVENTORY.md`, evidence addenda, and prior resume text.

The older files have already been used to compile the consolidated canonical. They must not remain active application inputs. Do not consult them to fill a gap, and do not revive superseded employers, projects, domains, metrics, wording, or tool attributions. If the consolidated canonical lacks a material fact, record the gap in coverage instead of fabricating evidence.

The final project architecture is only:

- `00-APPLICATION-ENGINE.md` for rules;
- `canonical.yaml` for all active facts and policies. `01-CANONICAL.md` is only a pointer; `archive/canonical-v2.md` is provenance, not an application input.

## Stage 1: Decode the job

Before selecting evidence, reconstruct what the employer is actually building and why. Write one internal hiring thesis that states the business problem, the system or workflow, the users, and the desired operating result.

Then reduce the JD to three to five non-duplicative **central buying criteria**. These are the outcomes or capabilities the employer is primarily paying for, not every keyword in the posting.

For each criterion, extract its **critical-path components**. A component is critical when removing it changes the workflow, prevents a stated input from becoming the required output, or breaks an explicitly repeated platform requirement. Do not allow a specific component to disappear inside a broad label. For example, `document automation` does not automatically cover OCR, and `enterprise data integration` does not make Azure Databricks optional when it is the named platform.

Classify every relevant JD item as **Stack item, capability requirement, both, or constraint**:

- **Stack item** - a named implementation technology: language, library, framework, model, provider, database, platform, cloud service, API, automation tool, observability product, deployment system, testing tool, or environment. Stack items are automatically authorized and never require a question.
- **Capability requirement** - work the candidate must actually perform or an outcome the system must produce. Capability requirements must be mapped to known work and may require one question when central and missing.
- **Both** - a named technology that is also a central operating responsibility. Mirror the technology automatically, then evaluate the responsibility separately as capability proof.
- **Constraint** - a factual eligibility, location, language, education, certification, seniority, or authorization condition.

Separately record:

- verified mandatory constraints;
- preferred or peripheral requirements;
- the workflow's inputs, decisions, systems, outputs, and users;
- business-team, data-team, platform-team, and end-user interactions;
- prototype, pilot, production, scaling, change-management, and adoption expectations;
- every explicitly named implementation technology and the function it serves;
- the expected seniority and ownership level;
- the likely title, domain, and career-pattern match expected in the applicant pool;
- the exact ATS terminology the final application must visibly use;
- the business result the role exists to improve.

Do not let a long tool list outweigh the central work of the role.

## Stage 2: Build the JD stack manifest and target architecture

Create a **Stack manifest** containing every implementation technology named anywhere in the JD, including the job overview, task list, qualifications, and technology section. Preserve the employer's exact spelling and product name. Do not filter the manifest through the canonical and do not remove a stack item because it was not recorded under an employer.

Before mapping evidence, create an internal target architecture using the employer's own stack and vocabulary. Include only the layers relevant to the JD, such as:

- source input or business trigger;
- ingestion and trusted-data layer;
- storage and database layer;
- compute and transformation layer;
- orchestration and workflow layer;
- LLM, agent, retrieval, or model layer;
- evaluation, guardrail, and human-decision layer;
- deployment and runtime layer;
- observability and failure-handling layer;
- user workflow, adoption path, and business outcome.

When the JD names a stack, this target architecture controls the visible technical story across every technology category, not only cloud. The JD's languages, libraries, frameworks, models, databases, APIs, orchestration, observability, deployment, testing, and environment choices become the implementation vocabulary for the application.

Apply the functional stack-retrofit policy in `canonical.yaml`. Treat every stack-manifest item as available. Never ask about a stack item.

Stack-retrofit rules:

- reproduce every stack-manifest item exactly in Skills;
- place the most central stack items in the Summary and retrofit them directly into the selected employer pipelines;
- translate architecture by function instead of preserving source-side vendor names mechanically;
- suppress irrelevant source-side vendors when they make the resume look aligned to a competing ecosystem;
- keep the employer, problem, ownership, workflow, output, scale, metric, and status unchanged;
- do not use stack retrofit to invent certification, years of use, tool-specific scale, a specialized feature, or a new business outcome;
- do not mix competing implementation stacks unless the JD explicitly values that breadth;
- do not describe the translation as a gap, migration, or apology.

The objective is not to show the recruiter that Lohith could theoretically transfer. The objective is to present an application already expressed in the environment the employer uses.

## Stage 3: Build the capability evidence map and pre-draft coverage ledger

Stack items do not require an evidence lookup. They are handled by the Stack manifest and universal retrofit authority.

Map every capability requirement and every critical-path work component to the strongest evidence. Mark each internally as:

- **Direct** - the evidence shows substantially the same capability or outcome in a comparable setting.
- **Retrofitted** - the underlying pipeline or capability is confirmed and will be expressed using the JD's exact implementation stack.
- **Transferable** - the underlying capability is demonstrated, but the domain, interface, or surrounding context differs and requires an explicit bridge.
- **Unsupported** - no defensible evidence supports the criterion.
- **Unknown** - the requirement or candidate fact is genuinely unresolved after checking the sources.

For each selected claim, maintain an internal trace to its source section. Do not output this trace, but do not draft a claim that cannot be traced.

Before drafting, create a **pre-draft coverage ledger** with these fields:

| Field | Required content |
|---|---|
| Requirement | Exact criterion or critical-path component |
| Criticality | Critical path, core, supporting, or peripheral |
| Evidence | Employer system, candidate-level capability, education, or confirmed project |
| Representation | Exact language, stack retrofit, or explicit capability bridge |
| Resume location | Summary, Skills, named employer bullet, project, or cover letter |

Every critical-path component must have a planned visible representation. It cannot be marked covered merely because a related term exists somewhere in the canonical.

Unknown is not negative evidence. If a critical capability remains Unknown and the answer could materially change the application, ask one targeted question before drafting. Stack items are never Unknown and must never trigger a question.

## Stage 4: Competitive fit classification

Begin every completed fit decision with exactly one line:

`Strong fit - <reason>.`

`Apply with reframe - <angle>.`

`Hard pass - <reason>.`

Use the following deterministic gate. Let `N` be the three to five central buying criteria.

### Strong fit

Use only when all are true:

- there is no verified blocker;
- the highest-priority criterion has Direct evidence;
- at least 60 percent of the central criteria have Direct evidence;
- every remaining central criterion has Retrofitted or Transferable evidence, with no Unsupported or material Unknown criterion;
- every critical-path capability has visible Direct, Retrofitted, or Transferable coverage;
- at least one recent professional result provides credible impact or scale for the role's primary work;
- the visible title, seniority, ownership, and career path would make Lohith look like a close candidate, not merely someone who could learn the job.

### Apply with reframe

Use when all are true:

- there is no verified blocker;
- the highest-priority criterion has Direct, Retrofitted, or Transferable evidence;
- at least 40 percent of the central criteria have Direct evidence;
- Direct plus Retrofitted plus Transferable evidence covers at least 80 percent of the central criteria;
- no more than one central criterion is Unsupported or materially Unknown;
- the title, domain, vendor, or seniority bridge can be made clear within a five-to-ten-second resume scan.

Use this label for strong capability with weaker competitive signaling. State the actual bridge angle, not generic optimism.

### Hard pass

Use when any is true:

- an explicit mandatory requirement conflicts with a verified fact, such as language, work authorization, location, credential, or availability;
- the role's primary identity is an unsupported discipline or genuinely different technical paradigm;
- two or more central buying criteria are Unsupported or materially Unknown;
- Direct plus Retrofitted plus Transferable evidence covers less than 80 percent of the central criteria;
- a non-vendor critical-path capability is Unsupported and cannot be credibly bridged;
- the required leadership, seniority, regulated-domain ownership, or formal people-management scope is materially beyond the evidence;
- a credible application would require changing titles, inventing domain experience, inventing outcomes, or making several unsupported inferential leaps.

A Stack manifest item is never a blocker and never lowers fit. Only the substantive work behind the stack, a mandatory constraint, or an unsupported central capability can do so. If the result is `Hard pass`, stop after the fit line and do not produce JSON.

## Universal stack retrofit

Universal stack retrofit is mandatory. It is not limited to cloud services, and it is not satisfied by adding a few target keywords beside an otherwise mismatched architecture.

The known work defines pipelines and outcomes. The JD defines how those pipelines are implemented and described for the target application.

Apply these rules:

1. **Mirror the complete stack.** Every named implementation technology from the Stack manifest must appear exactly in Skills.
2. **Retrofit central tools into proof.** Place the most important models, frameworks, databases, orchestration tools, cloud services, APIs, observability systems, deployment technologies, and environments directly into the relevant employer pipelines.
3. **Map by pipeline function.** Insert each tool where it logically performs work in the known pipeline. Do not scatter keywords without a functional relationship.
4. **Preserve impact.** Keep the canonical problem, ownership, scale, metric, output, and status while changing the implementation vocabulary.
5. **Remove competing noise.** Omit source-side stack names that weaken the target match unless the JD explicitly values multi-stack experience.
6. **Do not explain transfer.** Do not use `similar to`, `compatible with`, `equivalent to`, or tool-gap apologies.

This authority applies to every implementation category. Never ask about a stack item and never reject a role because the canonical does not list the JD's particular tool.

Stack retrofit does not automatically prove a new kind of work. If the JD centrally requires a capability absent from the known pipelines, such as extracting handwritten documents, performing a specialized analysis, owning regulated decisions, or operating another distinct workflow, follow the capability-question policy before drafting.

## Workflow reconstruction

Evidence is not a frozen library of resume bullets. Reconstruct the strongest defensible view of the real work around the JD.

For each relevant system, consider its actual:

- trigger or input;
- ingestion and data sources;
- transformation or decision logic;
- orchestration and scheduling;
- model or tool calls;
- APIs and integrations;
- state, cache, database, or ledger;
- validation, evaluation, and deterministic gates;
- retries, observability, and failure handling;
- security controls and claim boundaries;
- human approval or escalation;
- downstream action, delivery, or publication;
- business result, scale, and operating change.

For agentic or automation work, also reconstruct the maintainability story:

- what state is durable and where it lives;
- which stage contracts prevent a local change from silently breaking downstream behavior;
- which decisions are probabilistic and which controls are deterministic;
- how loops stop, retry, recover, or escalate;
- how execution becomes visible and diagnosable;
- which human decision remains in the path;
- how model, prompt, or workflow changes can be reviewed without rebuilding the whole system;
- how cost, context, memory, and repeated execution are controlled.

Do not claim that a system never fails. Show how its design reduces cascading failure risk, contains uncertainty, and makes maintenance safer.

Expose the components that prove the employer's central buying criteria. Suppress irrelevant implementation detail. This is a reconstruction of emphasis and technical story, not a terminology swap around the same generic bullets.

Permitted:

- writing a new sentence that combines source-supported components of the same role or system;
- using exact JD terminology for a capability that the evidence genuinely supports;
- emphasizing different workflow stages for different roles;
- describing the transferable engineering pattern while omitting an irrelevant domain.

Forbidden:

- combining unrelated employers or projects into one synthetic system;
- moving a metric, ownership claim, business outcome, production status, or user scale to a different workstream;
- using stack retrofit to invent an employer-specific certification, duration, tool-specific metric, new responsibility, or new business outcome;
- converting a prototype, pilot, planned workstream, or in-progress component into a completed production system;
- treating a technically coherent story as evidence when its components are not attributable to the same body of work;
- inventing abstract project wrappers around employment work.

## Stable professional spine

The default career story remains stable:

`production data pipelines -> applied LLM and safety systems -> zero-to-one AI automation -> one-to-ten multi-tenant agentic operations`

Tailoring changes the center of gravity, evidence selection, terminology, and technical depth. It does not reinvent Lohith as a different person for every JD.

Do not frame him as a single-tool specialist, SEO specialist, content specialist, WordPress specialist, or social-media specialist. Domains are context. The transferable pattern is understanding the full workflow, building the system, placing deterministic controls around model behavior, making failures observable, and preserving maintainability as the system changes.

Do not reconstruct a second professional spine from evidence deliberately removed from the active canonical.

## Scaling-stage handling

Each employer in the canonical has one primary scaling stage. Use it as an evidence-selection rule, not as decoration:

- Formula Dream is 0-to-1.
- Corominas, Think Round, and Cognizant are 1-to-10.

For a job description that values building from ambiguity, emphasize Formula Dream's creation of connected systems from manual processes. For a job that values scale, reliability, platform maturity, or operational leverage, emphasize the 1-to-10 evidence from Corominas, Think Round, or Cognizant.

Use `0-to-1` or `1-to-10` explicitly in the resume only when the job description rewards that language and the sentence still sounds natural. Never relabel a role merely to match a keyword.

## Corominas handling

For every resume using Corominas, use only the Corominas employer record and its linked facts, metrics, and boundaries in `canonical.yaml`:

1. Read and preserve the canon's identity.
2. Select only two to four capability blocks that directly serve the JD.
3. Use only metrics and formulations allowed by the canon.
4. Apply every exclusion and status boundary, including security-response and completion limits.
5. Use domain language only when the JD rewards that domain; otherwise describe the transferable work pattern.
6. Do not use every block, overload the role, or make three months appear to contain an entire invented career.
7. Do not apologize for the tenure. Let selected outcomes and scope carry the entry.

## Impact-first resume writing

Before drafting a generic architecture bullet, search the evidence for:

- volume or frequency;
- before-and-after time;
- manual effort removed;
- cost change;
- client, user, or portfolio scale;
- throughput or turnaround;
- adoption or coverage;
- reliability or failure containment;
- risk reduction;
- operational leverage.

Put the outcome, scale, or operational consequence in the first clause whenever it remains natural. A useful default structure is:

`impact or scale -> owned change -> technical proof`

If no numeric metric exists, state a concrete operational change instead of filling the bullet with architecture language. Each major bullet should answer: what became faster, cheaper, safer, more reliable, more scalable, or newly possible?

Derived metrics are allowed only when they are exact arithmetic from user-confirmed anchors belonging to the same workflow. Use conservative assumptions, show approximate language such as `about` or `roughly`, and never multiply several uncertain ranges to manufacture precision. If one missing boundary would unlock a materially stronger claim, use the targeted-question policy.

Do not lead with model counts, node counts, stage counts, assertion counts, tool counts, line counts, or test counts unless the count itself is central to the JD and explicitly claimable.

## Recruiter-first language

The resume is read by a recruiter before it is examined by a technical specialist. Every sentence must make sense on the first read while still giving enough technical proof for the second reader.

- Use one main idea per sentence.
- Use concrete subjects and verbs. Say who changed what and what happened because of it.
- Put the operational result or scale before dense implementation detail.
- Prefer familiar words over abstract phrases and stacked technical nouns.
- Explain the capability in plain language before naming architecture components.
- Aim for roughly 20 to 40 words when that is enough to explain the action, technical mechanism, and consequence. This is writing guidance, not a rejection or retry rule.
- Do not join several weak claims with commas to make one oversized bullet.
- Avoid vague phrases such as `drove transformation`, `leveraged cutting-edge technology`, `architected scalable solutions`, `enabled innovation`, or `delivered end-to-end excellence` unless the sentence immediately states the concrete change and result.
- Technical terminology is allowed when it names real work, but it must not make the recruiter decode the sentence.

Read every summary sentence, bullet, and cover-letter sentence once at normal speed. If its meaning is not immediately clear, rewrite it. If a simpler sentence has the same factual meaning and impact, use the simpler sentence.

## One-page density and selection limits

The resume must be ATS-safe, readable at normal size, and understandable in five to ten seconds. Prefer deletion over compression.

- Summary: two to three substantive sentences, aiming roughly for 55 to 80 words when the page permits. This is writing guidance, not a rejection or retry rule.
- Skills: use compact categories, but include every Stack manifest item. Complete JD stack coverage overrides any default item limit.
- Experience: include every employer in the active canonical chronology. Relevance controls space, not presence.
- Each employer: one to four bullets according to the number and importance of buying criteria it proves.
- A highly relevant older role may receive more bullets than a recent but less relevant role.
- Do not force descending counts such as 4-3-2-1, equal counts, or any other chronology-based pattern.
- Total experience bullets: no global cap or target. Select every distinct useful point that fits after reserving all employers, Skills, one project, and education; never exceed four bullets for one employer.
- Projects: include one JD-relevant independent local/GitHub prototype from the authorized pattern in `canonical.yaml`.
- Do not repeat the same claim, metric, workflow, or tool list across Summary, Skills, Experience, and Projects.

Allocate the bullet budget from the pre-draft coverage ledger. Requirement coverage, target-stack proof, professional ownership, deployment context, and defensible impact determine space. Recency breaks close ties but never imposes a taper.

## Summary

Write a professional positioning statement, not a compressed achievements section.

It should establish:

- the target identity consistent with the stable professional spine;
- the breadth or specialization relevant to the JD;
- the business or technical problems Lohith solves;
- the most important supported capability pattern.

Include the two to five stack items most central to the employer's workflow naturally in the Summary. Do not turn the Summary into a complete tool list; Skills carries the full Stack manifest.

Do not duplicate detailed metrics or employer-specific accomplishments. Avoid generic phrases such as `results-driven`, `passionate`, `innovative professional`, `cutting-edge`, or `scalable AI-native solutions`.

## Skills

Skills exist for ATS indexing and rapid verification. Experience exists for proof.

- Reproduce every named implementation technology in the JD exactly, regardless of whether it appears in an employer subsection of the canonical.
- Cover 100 percent of the Stack manifest. This requirement applies to every technology category, not only cloud, data, observability, AI, or automation.
- Preserve exact product names and useful ATS variants when space allows, such as the full name plus a standard abbreviation.
- Group the mirrored stack into job-relevant categories so it remains readable.
- Suppress equivalent source-side vendors when listing them would dilute the target-stack signal.
- Omit impressive but irrelevant tools that the JD does not request.
- Do not attach invented years, certifications, proficiency levels, or metrics to a stack item.

## Experience bullets

- Begin with ownership, impact, or scale rather than passive participation.
- Make the business meaning understandable before adding technical detail.
- Prove the JD's central buying criteria instead of displaying general AI sophistication.
- Use technically precise language only when it strengthens credibility.
- Vary evidence selection and order materially between different roles; do not put the same evidence package in different vocabulary.
- Reconstruct technical framing through the target architecture. Retrofit the JD's exact central stack items directly into the selected employer pipelines while preserving each employer's real problem, outcome, scale, and status.
- Do not require the exact target tool to appear in that employer's canonical subsection. The universal stack-agnostic authority explicitly permits the retrofit.
- Omit source-side vendor names that are not required to understand or substantiate the accomplishment and that make the application look aligned to the wrong ecosystem.
- Assign bullets from the coverage ledger. Every major buying criterion should have a clearly identifiable proof point, and no critical-path component may remain merely implied.
- Preserve authoritative titles and dates. Use a title variant only when the evidence source explicitly authorizes that variant for the target role; never create another one.
- Never omit an employer from the canonical chronology. Compress less relevant roles instead.

Agentic terminology such as tool use, memory, evaluation, context management, guardrails, human review, observability, stopping conditions, model routing, and bounded autonomy is useful only when it describes the actual system.

## Projects

The canonical authorizes one JD-relevant independent prototype based on Lohith's confirmed working pattern: before a larger implementation, he builds a small local version of the target workflow and adds it to GitHub. Retrofit the exact JD stack to the local workflow and state its useful output. Do not invent a project date, repository URL, employer, company scale, or employer metric. Do not copy an employer bullet. The public item remains `{name, period, bullets}` and uses an empty period when no date is confirmed.

## Targeted boundary-question policy

Never ask about a Stack manifest item. Languages, libraries, frameworks, models, providers, databases, platforms, cloud services, APIs, orchestration tools, automation tools, observability products, deployment systems, testing tools, and environments are automatically authorized for retrofit.

Ask a question only when a genuinely unresolved fact would:

- change the fit classification;
- resolve a source conflict that would appear in the application;
- verify a mandatory constraint;
- establish a critical kind of work that cannot be inferred from the known pipelines;
- unlock one materially stronger impact, scale, ownership, or status claim.

First search the known pipeline evidence. Ask one narrow question only when a central capability remains absent. The question must ask about the work performed, workflow, ownership, or outcome - never whether Lohith knows a named stack tool.

If the missing capability is not central, omit it and continue. If it is central, pause for the one necessary answer. Examples include OCR as the required input mechanism, a specialized domain workflow, regulated clinical authority, a mandatory language, or a legally material work-authorization fact.

## Personal details and address routing

All personal and administrative facts belong in `canonical.yaml`, including name, phone, LinkedIn, education, current location, citizenship, immigration status, work authorization, relocation preference, and any approved alternate correspondence address.

The resume header and application answers must use those facts exactly. Do not infer work authorization from an address.

For a job physically located in the Netherlands:

- use the confirmed Netherlands correspondence address from the canonical in the resume header;
- do not describe that address as Lohith's current residence unless the canonical explicitly says so;
- do not state or imply Dutch or EU work authorization;
- preserve the canonical fact that the German Chancenkarte does not provide unrestricted work authorization in the Netherlands;
- evaluate any Dutch authorization or sponsorship requirement honestly and separately from address selection.

For jobs outside the Netherlands, use the canonical current-location address unless the canonical gives another explicit country rule. If a Netherlands role is being prepared before the alternate address has been added to the canonical, ask for that one address and do not invent it.

## Application output contract

For every role worth applying to, output exactly one fenced JSON block immediately after the fit line. Do not add commentary before the fit line or after the JSON.

Use this exact root schema and do not add, remove, or rename keys:

```json
{
  "company_name": "...",
  "resume": {
    "summary": "...",
    "skills": [
      {
        "label": "...",
        "value": "comma separated skills"
      }
    ],
    "experience": [
      {
        "title": "...",
        "company": "...",
        "period": "...",
        "bullets": [
          "..."
        ]
      }
    ],
    "projects": [],
    "education": [
      {
        "degree": "...",
        "school": "...",
        "year": "..."
      },
      {
        "degree": "...",
        "school": "...",
        "year": "..."
      }
    ]
  },
  "cover_letter": {
    "date": "...",
    "company_address": "...",
    "salutation": "...",
    "paragraphs": [
      "...",
      "...",
      "..."
    ]
  }
}
```

Additional output rules:

- JSON must parse without repair and contain no trailing commas or comments.
- Preserve the established downstream project-item shape when `projects` is populated; do not invent new root keys.
- Use an empty string for an unknown company address rather than inventing one.
- Use `Dear Hiring Team` when no named recipient is provided.
- Use the actual application date.
- Populate education and all rendered header details from `canonical.yaml`; the schema examples are placeholders, not evidence.
- Use plain hyphens only, not en dashes or em dashes, throughout generated application content.

## Cover letter

Use no more than three short paragraphs:

1. Show why the role maps to work already done.
2. Give one strong, concrete example with impact.
3. Explain why the company's problem is a logical next fit.

Do not repeat the full resume, apologize for transferable tools, invent company knowledge, or use generic enthusiasm. Company-specific claims must come from the JD or another current authoritative source.

When the JD names a target stack, use that exact stack in the cover letter and connect it to Lohith's strongest relevant scale, workflow, or adoption evidence. Do not explain that another vendor is similar when candidate-level experience with the target stack is already confirmed.

## Truthfulness boundaries

Never invent or alter:

- employers, titles, dates, or employment type, except for a title variant explicitly authorized by the evidence source;
- degrees, credentials, location, languages, or work authorization;
- years of experience, or people-management scope;
- causation that the evidence supports only as contribution or enablement.

## Deterministic final validation

Do not return the application until every check passes. Fix failures by rewriting or deleting content. If a material failure requires a missing user fact, ask one targeted question and defer the draft.

### 1. Fit gate

- Exactly three to five central buying criteria were identified.
- The employer's business outcome and end-to-end workflow were reconstructed.
- Each criterion was decomposed into critical-path components.
- Every capability criterion and critical work component has a Direct, Retrofitted, Transferable, Unsupported, or Unknown status.
- No specific workflow component was swallowed by a broad category label.
- The selected fit label satisfies its numerical and qualitative rules.
- Capability fit and competitive fit were both evaluated.

### 2. Source gate

- Every factual claim traces to `canonical.yaml` or to one narrow current-session correction that will be added there.
- JD stack terms are authorized through the canonical's universal pipeline and stack-agnostic authority.
- Corominas claims obey the dedicated Corominas section and its boundaries.
- No deprecated evidence file, prior resume, or generated bullet was used as authority.
- No internal source conflict or explicit boundary was silently overridden.

### 3. Universal stack-retrofit gate

- A Stack manifest was created from every named implementation technology in the entire JD.
- Every Stack manifest item appears exactly in Skills: 100 percent stack coverage is mandatory.
- The most central stack items appear in the Summary or relevant experience bullets.
- Central stack items were retrofitted directly into the selected employer pipelines at logically correct workflow stages.
- The rule was applied across languages, libraries, frameworks, models, databases, cloud, APIs, orchestration, automation, observability, deployment, testing, and environments - not merely one technology family.
- Irrelevant source-side vendors were suppressed.
- The resume does not mix competing stacks unless the JD explicitly values that breadth.
- No tool-gap apology, `compatible with`, `similar to`, or `equivalent to` language appears.
- No stack item triggered a clarification question.
- Stack retrofit did not invent certification, years of experience, employer outcome, metric, status, responsibility, or specialized platform behavior.

### 4. Selection and identity gate

- The page preserves the stable professional spine.
- Every employer in the canonical chronology remains present, with space allocated by JD relevance.
- A pre-draft coverage ledger assigned every critical requirement to visible resume evidence.
- Evidence proves the employer's central work rather than general technical breadth.
- Bullet counts follow requirement coverage and are not a mechanical chronological taper.
- Corominas uses only two to four relevant blocks and is not overloaded.
- One independent local/GitHub prototype follows the canonical pattern and contains no employer metric, invented date, or invented URL.
- No deleted legacy employer, domain, tool family, or project has been restored from memory or a deprecated source.
- The resume would still look like the same person across applications.

### 5. Impact and credibility gate

- Every major bullet contains a defensible result, scale anchor, or concrete operational change.
- Strong available metrics are not buried or left unused.
- Derived metrics use only confirmed same-workflow anchors and appropriately approximate language.
- No short role is made implausibly responsible for the candidate's entire career.

### 6. Density and scan gate

- Summary, skills, every-employer coverage, bullet count, and project count stay within the one-page limits.
- The top third of the resume proves the highest-priority buying criterion.
- The target environment and exact central stack are visible in the top third.
- A recruiter can understand the match in five to ten seconds without several inferential jumps.
- Irrelevant tools, repeated claims, filler, and architecture-only bullets were removed.
- Every sentence passes the one-read plain-language test and most bullets stay within the stated word range.

### 7. JD-versus-resume audit

Run this as a separate pass after drafting. Compare the finished resume with the Stage 1 JD model; do not validate from memory.

- Every critical-path component is explicit somewhere the recruiter will see.
- Every core buying criterion has at least one identifiable proof point.
- Every Stack manifest term appears in Skills, and the central stack appears with enough prominence for ATS and human scanning.
- No requirement is counted as covered merely because a broad adjacent capability appears.
- No central requirement is present only in the Skills section when the employer expects demonstrated delivery.
- Business discovery, prototyping, production movement, stakeholder enablement, adoption, or change management are represented when the JD makes them central.
- The strongest relevant older employer receives sufficient space; recency did not force a 4-3-2-1 pattern.
- A project is included only if it improves critical coverage more than the experience content it displaces.

If any critical component is absent or merely implied, the application fails. Rewrite the plan and draft, or ask one targeted question only when the missing item is a genuinely unresolved non-vendor capability.

### 8. Output gate

- The fit line uses one approved format.
- `Hard pass` output stops after the fit line.
- Application JSON matches the fixed root schema exactly and parses successfully.
- Dates are unchanged, and title variants appear only where the canonical explicitly authorizes them.
- The `projects` key is present and an empty projects heading will not render.
- Personal details and education match the canonical exactly.
- A Netherlands address, when used, is not presented as proof of residence or work authorization.
- The cover letter has no more than three short paragraphs.
- Generated application content uses plain hyphens only.
- There is no commentary after the JSON.
