# BrAIny Buddy

BrAIny Buddy is an n8n-powered Telegram learning assistant.

- Bot: [@AskBrAInyBot](https://t.me/AskBrAInyBot)
- Workflow export: `BrAIny Buddy - Main Bot v2.json`
- Main storage tables: `learning_materials`, `quiz_attempts`

## Submission Files

- [task.md](task.md) - original task description transcribed from screenshots.
- [report.md](report.md) - implementation journey and technical report.
- [n8n-llm-prompts.md](n8n-llm-prompts.md) - Teacher and Examiner LLM prompts used in the workflow.
- [atlas-telegram-web-test-prompt.md](atlas-telegram-web-test-prompt.md) - prepared external Telegram Web testing prompt.

## How to Use the Bot

1. Open [@AskBrAInyBot](https://t.me/AskBrAInyBot) in Telegram.
2. Send `/start` to see the welcome message.
3. Send a public learning URL:

   ```text
   /learn https://docs.python.org/3/tutorial/controlflow.html
   ```

4. Wait for the processing message and the generated summary.
5. Use the `Start quiz` button below the summary, or send:

   ```text
   /quiz
   ```

6. If `/quiz` is used, choose one of the saved topics from the inline buttons.
7. Answer the five A/B/C/D questions.
8. Read the final score and per-question feedback.

## Useful Commands

```text
/start
/help
/learn <url>
/quiz
```

`/help` is included as a convenience command. The task-required commands are `/start`, `/learn <url>`, and `/quiz`.

## Expected Behavior

- `/learn <url>` fetches the page, extracts readable text, asks the Teacher AI role for a summary, key points, concepts, and difficulty level, then saves the material.
- Re-submitting the same normalized URL for the same user returns the existing saved summary instead of fetching and summarizing it again.
- `/quiz` shows saved topics with paginated inline buttons.
- Choosing a topic asks the Examiner AI role to generate five multiple-choice questions.
- Answers are stored in `quiz_attempts`; the bot calculates a percentage score and explains incorrect answers.
- Completed quiz attempts are immutable. Pressing old A/B/C/D buttons after a quiz is finished does not alter the saved result.

## Guardrails

The workflow includes several practical guardrails:

- accepts exactly one URL after `/learn`;
- strips common tracking parameters and URL fragments;
- rejects local/private, Telegram, media, archive, and executable URLs;
- sends a processing message before slower fetch or AI work;
- handles fetch failures with a Telegram response;
- rejects pages with too little readable content;
- paginates saved topics;
- prevents stale or duplicate answer callbacks from changing quiz progress.

## Import Notes

The exported workflow uses n8n Connect for the OpenAI-backed model nodes, so no separate LLM API key is required.

The raw Telegram Bot API HTTP Request node for dynamic topic buttons uses this n8n variable:

```text
$vars.TELEGRAM_BOT_TOKEN
```

The variable should contain the Telegram bot token only. The workflow URL includes the required `bot` prefix:

```text
https://api.telegram.org/bot{{ $vars.TELEGRAM_BOT_TOKEN }}/sendMessage
```

After importing the workflow into another n8n workspace, remap Telegram credentials if needed and make sure the `learning_materials` and `quiz_attempts` Data Tables exist.

## Test Links

These links were useful for positive-path testing:

```text
/learn https://docs.python.org/3/tutorial/controlflow.html
/learn https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Variables
/learn https://www.postgresql.org/docs/current/tutorial-join.html
```

This link is useful for the fetch-error path:

```text
/learn https://example.com/article
```
