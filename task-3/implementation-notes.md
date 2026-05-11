# BrAIny Buddy Implementation Notes

Date: 2026-05-11

These notes capture the current implementation journey for the final task report. They are a working log, not the final submission report.

## Current status

- Bot display name: BrAIny Buddy
- Telegram username: @AskBrAInyBot
- Bot URL: https://t.me/AskBrAInyBot
- n8n workflow draft: BrAIny Buddy - Main Bot v2
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

- `/quiz` is still a placeholder.
- `topic:<materialId>` callback handling is still a placeholder.
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
