# BrAIny Buddy Implementation Notes

Date: 2026-05-11

These notes capture the current implementation journey for the final task report. They are a working log, not the final submission report.

## Current status

- Bot display name: BrAIny Buddy
- Telegram username: @AskBrAInyBot
- Bot URL: https://t.me/AskBrAInyBot
- n8n workflow draft: BrAIny Buddy - Main Bot v2
- As of 2026-05-12, `/quiz` works end-to-end and the next focus is improving `/learn` output formatting.
- The `/learn` summary output was cleaned up so key points and concepts render as readable bullet lists instead of raw JSON strings.
- A second `/learn` test with `https://web.dev/learn/html/semantic-html` worked, giving evidence that the workflow is not tied to the original MDN JavaScript test URL.
- After adding a second material, `/quiz` still showed only one saved topic, so the topic-list branch needs a multi-row retrieval/rendering fix.
- Data Tables created:
  - learning_materials
  - quiz_attempts

## Completed

- The task description screenshots were transcribed into `task.md`.
- Telegram bot identity was created through BotFather.
- n8n Data Tables were created for persistent storage.
- The `/learn <url>` branch now works through:
  - Telegram Trigger
  - Normalize Telegram Update
  - Command Router
  - Extract URL
  - Fetch URL Content
  - Clean HTML Content
  - Teacher Agent - Summarize Material
  - Parse Teacher JSON
  - Prepare Material Data
  - Save to learning_materials
  - Send Summary with Quiz Button
- A real MDN JavaScript article test produced a material-specific summary in Telegram.
- The learning material row was saved in `learning_materials`.
- The Telegram summary message includes a Start quiz inline button.
- The `/quiz` route now responds with "Choose a saved topic:" and shows at least one saved-topic inline button.
- Pressing the Start quiz inline button reaches the topic callback route, but that route still sends the placeholder "Topic callback coming soon!" message.
- The topic callback branch now parses `topic:<materialId>` and loads the matching row from `learning_materials`.
- The Examiner quiz generation step now produces valid five-question quiz JSON for the selected material.
- The workflow now saves a quiz attempt and sends the first question to Telegram.
- The Examiner prompt interpolation was corrected by preparing a `chatInput` field before the Basic LLM Chain; generated questions now reference the selected MDN JavaScript material instead of literal n8n expressions.
- A/B/C/D inline answer buttons are now visible on the first quiz question.
- The first answer callback reaches the next-question path, but the `Send Next Quiz Question` node failed because its text evaluated to `undefined` and Telegram rejected inline buttons without callback data.
- The answer-flow issue was traced to the `Process Answer` Code node being disabled. Re-enabling it allowed the branch to produce the expected next-question text and callback fields.
- A full five-question quiz was completed in Telegram, producing a final score and explanations for incorrect answers.

## Tool roles and observations

- Atlas agentic mode was attempted for n8n Data Table setup but was not useful for the UI-heavy process.
- Claude Chrome Extension handled the n8n Data Table UI setup successfully and reported several n8n UI gotchas.
- n8n AI Builder generated the first workflow drafts but repeatedly required manual correction.
- Codex was used for planning, prompts, troubleshooting, code-node snippets, and maintaining this implementation log.

## Notable gotchas

- n8n Data Table setup had UI friction:
  - type selectors behaved like custom Vue comboboxes rather than native selects,
  - delete-column hit zones did not align visually,
  - table columns required horizontal scrolling to audit.
- n8n AI Builder repeatedly failed during small edit prompts with:
  - `Cannot read properties of null (reading 'replace')`
- The same n8n AI Builder error also blocked later attempts to generate the quiz-start branch, so further workflow construction moved to manual node-by-node editing.
- The generated workflow originally used an output parser that failed with:
  - `"[object Object]" is not valid JSON`
- The parser approach was replaced with normal Code nodes that parse raw AI JSON output.
- Several generated Code nodes used an incompatible input style and had to be corrected to use `$input.first()` and named-node lookups.
- The Teacher Agent initially failed with:
  - `Bad request - please check your parameters`
  - Root cause: an unsupported model parameter in the generated model/agent configuration.
  - Fix: the unsupported parameter was removed manually.
- The `/learn` branch initially saved to the database but did not reply to Telegram because no send-message node was connected after persistence.

## Current limitations

- `/quiz` route is reachable and displays saved topic buttons.
- `topic:<materialId>` callback handling parses the material id, loads the saved material, generates five relevant quiz questions, saves an attempt, and sends the first question.
- Answer callbacks now store responses, advance through the remaining questions, and calculate final score with per-question explanations.
- `answer:<attemptId>:<questionIndex>:<optionKey>` callback handling is still a placeholder.
- `quiz_attempts` exists but is not used yet.
- Key points and concepts are currently displayed as raw JSON strings in the Telegram summary; this is functional but should be formatted more cleanly later.
- The workflow is not yet ready for final export or publication as a complete task submission.

## Next planned work

1. Implement `/quiz` to load saved materials from `learning_materials` and show topic buttons.
2. Implement `topic:<materialId>` callbacks to generate a five-question quiz with the Examiner role.
3. Save quiz attempts to `quiz_attempts`.
4. Implement `answer:<attemptId>:<questionIndex>:<optionKey>` callbacks.
5. Calculate final score and send per-question feedback.
6. Export the n8n workflow JSON into this repository.
7. Write README usage instructions.
8. Write the final implementation report.
