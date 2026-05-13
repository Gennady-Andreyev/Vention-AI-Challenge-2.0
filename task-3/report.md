# BrAIny Buddy Implementation Report

## Overview

BrAIny Buddy was built as an n8n workflow that delivers an AI-powered personal learning assistant through Telegram. The bot accepts learning materials as URLs, summarizes them through a Teacher AI role, saves the resulting material, and generates five-question multiple-choice quizzes through an Examiner AI role.

The final bot is available at [@AskBrAInyBot](https://t.me/AskBrAInyBot). The workflow export is stored as [`BrAIny Buddy - Main Bot v2.json`](<BrAIny Buddy - Main Bot v2.json>).

## Final State

The workflow supports the required commands:

- `/start` shows onboarding instructions.
- `/learn <url>` fetches a public learning page, extracts content, summarizes it, saves it, and returns a formatted summary with a `Start quiz` button.
- `/quiz` lists saved topics and lets the user pick one for quiz generation.

Two n8n Data Tables persist state:

- `learning_materials` stores submitted materials, extracted content, summaries, key points, concepts, difficulty, URLs, user IDs, and chat IDs.
- `quiz_attempts` stores generated questions, answers, current quiz position, status, and score.

The workflow also includes usability and safety guardrails that go beyond the minimum task: URL normalization, invalid URL handling, fetch-error handling, weak-content detection, duplicate URL reuse, paginated topic selection, quiz-generation progress messages, and immutable completed quiz attempts.

## Implementation Journey

The work started by transcribing the task description into [task.md](task.md) and planning the workflow shape before building in n8n. The core design used two explicit AI roles:

- the Teacher role for material summarization;
- the Examiner role for quiz generation and explanations.

Data Tables were created early because persistence was central to the task. The table setup was more UI-sensitive than expected. Atlas agentic mode was attempted for this setup but was not effective in the n8n UI. A Claude Chrome extension handled the Data Table creation successfully and surfaced several UI gotchas, including custom combobox behavior, column scrolling, and imprecise delete-column hit zones.

n8n AI Builder helped generate early workflow drafts, and this was roughly an order of magnitude faster than building the first canvas manually. However, the drafts were not production-ready. Several generated pieces required manual correction. The most persistent builder failure was:

```text
Cannot read properties of null (reading 'replace')
```

After that, the implementation moved into a manual, node-by-node loop. Codex was used with the GPT-5.5 model configured to Extra High intelligence. Codex planned the next steps, generated prompts for n8n AI when useful, wrote large JavaScript Code-node snippets, explained n8n syntax and data flow, interpreted execution failures, designed test cases, and drafted the final documentation. n8n itself remained the implementation surface and runtime.

Most troubleshooting happened by sending screenshots of the n8n editor, node configuration panels, execution logs, and Telegram behavior into the same Codex chat. This proved to be the most effective debugging loop. Codex was especially helpful at reading n8n-specific symptoms from screenshots and translating them into concrete node changes, often producing JavaScript snippets and expressions that worked without user-side rewriting. At the same time, the user still had to steer the solution. Several times Codex was course-corrected toward simpler choices: reusing existing nodes, keeping the workflow drier, avoiding extra branches where a direct connection would do, and choosing straightforward n8n-native behavior over more elaborate abstractions.

The report preparation was also handled deliberately. At the beginning of the task, Codex was asked to keep enough context to assemble a final report. During the session, progress was saved into a private working log for decisions, failures, fixes, and test results. The entire implementation happened in a single long Codex conversation, and the chat auto-compacted context several times. The working log made the final [README.md](README.md) and this report possible without reconstructing the chronology from memory.

## Material Processing

The `/learn` branch now follows this high-level path:

```text
Telegram Trigger
-> Normalize Telegram Update
-> Command Router
-> Extract URL
-> Is URL Valid?
-> Find Existing Material Early
-> Route Existing Material
-> Has Existing Material?
```

If the material already exists for the same user and normalized URL, the workflow immediately returns the saved summary. This avoids another fetch and avoids another Teacher AI call.

For new materials, the flow continues:

```text
Send Processing Message
-> Fetch URL Content
-> Check Fetch Result
-> Is Fetch OK?
-> Clean HTML Content
-> Is Content Readable?
-> Teacher Agent - Summarize Material
-> Parse Teacher JSON
-> Prepare Material Data
-> Find Existing Material
-> Choose Material ID
-> Upsert learning_materials
-> Prepare Fresh Material Response
-> Send Summary with Quiz Button
```

The late `Find Existing Material` step remains intentionally. It preserves an existing `materialId` during upsert, which keeps old `topic:<materialId>` callbacks and quiz history stable.

## Quiz Flow

The `/quiz` branch loads saved materials for the user and builds a paginated topic picker. The native Telegram node was initially configured around one button at `[0][0]`, which meant only one saved material appeared. The final implementation sends the topic list through the Telegram Bot API using an HTTP Request node with a raw JSON body. This made the dynamic `reply_markup.inline_keyboard` array work correctly for multiple buttons and pagination.

Once a topic is selected, the workflow loads the material, sends an interactive "Generating a 5-question quiz..." message, builds the Examiner prompt, generates five questions, saves a quiz attempt, and sends questions one at a time with A/B/C/D inline buttons.

Completed quiz attempts are now immutable. A validation step checks status, current question index, duplicate taps, and stale callbacks before `Process Answer` can update the quiz. If the user taps old buttons after finishing a quiz, the bot replies that the quiz is already complete instead of changing the score.

## AI Prompting and Parsing

The workflow uses n8n Connect for the OpenAI-backed model nodes, so no separate LLM API subscription was required.

The initial structured-output-parser approach was fragile. The Teacher output parser failed with:

```text
"[object Object]" is not valid JSON
```

The final workflow instead asks both AI roles to return raw JSON and then parses that output with Code nodes. `Parse Teacher JSON` validates the Teacher shape, and `Parse Quiz JSON` validates that the Examiner produced exactly five questions, four A/B/C/D options per question, a valid correct answer, and explanations.

The Examiner prompt was moved into a `Prepare Examiner Prompt` Code node after an earlier version generated questions about literal n8n expressions such as `{{ $json.title }}`. Building `chatInput` in code ensured that the model received the selected material values rather than unresolved workflow syntax.

The Teacher prompt also needed a calibration pass after functional testing. Beginner and intermediate materials were classified correctly, but advanced materials were repeatedly marked as intermediate. That led to a focused back-and-forth: the prompt was expanded from a simple rubric into a domain-independent difficulty classifier based on reader prerequisites, reasoning depth, and operational risk. The n8n node configuration was then checked to confirm that the updated prompt was actually present in the Teacher Agent, that the chat model was connected, that memory/tools were not involved, and that the downstream Code parser still handled the raw JSON output. After this adjustment, advanced classification worked as expected. This was a good example of a workflow that was technically correct but still needed qualitative prompt tuning.

## What Worked

The strongest parts of the final solution came from combining n8n's visual workflow model with carefully scoped Code nodes. The Code nodes were useful for URL normalization, HTML cleanup, JSON parsing, quiz state validation, and Telegram payload preparation.

The raw Telegram Bot API HTTP Request was also a useful pivot. It solved the dynamic topic-list problem more cleanly than trying to coerce the native Telegram node into accepting a fully dynamic keyboard.

Pagination became a valuable addition even though it was not part of the original task text. Once saved materials persisted, the topic list could grow quickly. Paginating the inline buttons made `/quiz` easier to use and avoided an unbounded Telegram message.

The guardrail work substantially improved the bot experience. Invalid inputs, unreachable pages, weak content, duplicate URLs, long AI calls, and stale answer buttons now produce intentional user-facing behavior instead of confusing silence or state corruption.

From an education perspective, the Codex-guided manual path was more valuable than the n8n AI Builder path. n8n AI was much faster for producing an initial workflow shape, but Codex explained each step and let the user implement the changes manually in the editor. That made the final workflow easier to understand, debug, and defend. The user also caught details that the AI guidance initially missed, especially detailed execution logs, unusual system behavior, and opportunities to simplify the design.

## What Did Not Work

n8n AI Builder was helpful for rough drafts but unreliable for precise workflow repair. It repeatedly hit the `Cannot read properties of null (reading 'replace')` failure and sometimes generated nodes with parameters that did not match the actual model or node behavior. Its speed was still useful, but the educational and debugging value came primarily from the Codex-guided manual implementation loop.

Atlas was not effective for the n8n setup phase. A later Atlas Telegram Web test plan was prepared in [atlas-telegram-web-test-prompt.md](atlas-telegram-web-test-prompt.md), but it could not be executed because the monthly usage limit had been reached.

The native Telegram node was not a good fit for the fully dynamic saved-topic list. It worked well for fixed A/B/C/D quiz buttons, but the topic picker needed a raw Bot API request to send an arbitrary inline keyboard.

The first duplicate-handling idea tried to solve duplicates during pagination. That caused overlap and made the topic list harder to reason about. The final design moved deduplication to the write path instead: materials are upserted by `userId + url`, while pagination remains simple page slicing.

## Notable Gotchas

Telegram send nodes replace the current item with Telegram API response data. This caused downstream nodes to lose fields such as `url` unless they referenced earlier named nodes explicitly, for example `$('Extract URL').first().json.url`.

n8n's Code node runtime did not expose JavaScript's `URL` constructor in this environment. The URL guardrail was rewritten with regex parsing instead.

Telegram parse mode caused intermittent entity parsing failures when summaries contained arbitrary documentation text. Removing parse mode from Telegram messages made the flow more robust.

n8n Data Table upsert improved duplicate handling but is not a full database-level uniqueness guarantee under concurrent writes. A semi-concurrent `/learn` stress test exposed that limitation. For the challenge scope, URL reuse is handled practically in the workflow; a production version would use a database with a unique constraint on `(userId, normalizedUrl)`.

## Testing Summary

Manual Telegram testing covered:

- `/start` and `/help`;
- valid `/learn` submissions from MDN, Python documentation, PostgreSQL documentation, GitHub documentation, and web.dev;
- invalid `/learn` inputs with multiple URLs;
- unreachable URL handling with `https://example.com/article`;
- weak-content handling;
- duplicate URL reuse without another Teacher call;
- `/quiz` topic listing and pagination;
- topic selection through inline callbacks;
- full five-question quiz completion;
- final score and explanations;
- old answer-button taps after quiz completion.

The workflow remained active after the final export, and the exported JSON was checked for Telegram-token-shaped secrets before submission.

## Submission Artifacts

- [task.md](task.md): transcribed task description.
- [`BrAIny Buddy - Main Bot v2.json`](<BrAIny Buddy - Main Bot v2.json>): exported n8n workflow.
- [README.md](README.md): usage and import notes.
- [report.md](report.md): implementation report.
- [n8n-llm-prompts.md](n8n-llm-prompts.md): recorded Teacher and Examiner prompts.
- [atlas-telegram-web-test-prompt.md](atlas-telegram-web-test-prompt.md): saved independent Telegram test plan.
- `.githooks/pre-commit`: repository hook that blocks staged JSON files containing Telegram token-shaped secrets.
