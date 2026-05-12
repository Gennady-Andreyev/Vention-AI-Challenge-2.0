# Atlas Telegram Web Test Prompt

This prompt was prepared for an external Atlas run against Telegram Web. It was not executed at the time because the monthly Atlas usage limit had been reached.

```text
You are testing a Telegram bot in Telegram Web.

Bot under test:
BrAIny Buddy
Telegram username: @AskBrAInyBot
Bot URL: https://t.me/AskBrAInyBot

Critical safety constraints:
- I am using my real Telegram account.
- Only interact with the chat whose visible title or username is BrAIny Buddy / @AskBrAInyBot.
- Do not open, click, read, search, message, archive, delete, pin, mute, or interact with any other Telegram chat, channel, group, contact, bot, or conversation.
- Do not click Telegram sidebar chats.
- Do not use Telegram global search unless the bot chat is not already open, and then search only @AskBrAInyBot.
- If you land anywhere outside @AskBrAInyBot, stop immediately and ask me to navigate back.
- Do not click external links or previews inside messages.
- Do not contact BotFather or any other bot.
- Do not change account or chat settings.
- Do not delete messages or clear history.
- Do not send personal data, credentials, tokens, or secrets.
- If unsure whether the current chat is @AskBrAInyBot, stop and ask for confirmation.

Testing goal:
Validate BrAIny Buddy from a real Telegram user perspective, especially /learn with many different URLs, saved-topic deduplication, topic ordering, and pagination.

Important testing behavior:
- Send one command at a time.
- After each /learn command, wait for the bot's reply before sending the next link.
- If a link fails, record the failure and continue unless three links fail consecutively.
- Do not start a quiz after every /learn; that would be noisy and unnecessary.
- After the batch, use /quiz to test topic listing and pagination.
- Complete only 1 or 2 quizzes, not all topics.

Initial checks:
1. Open only:
https://t.me/AskBrAInyBot

2. Confirm the visible chat identity is BrAIny Buddy or @AskBrAInyBot.

3. Send:
/start

Record whether the welcome/help message appears.

Batch /learn test:
Send these one by one, waiting for a bot response after each:

1.
/learn https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Headings_and_paragraphs

2.
/learn https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Basic_selectors

3.
/learn https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/What_is_JavaScript

4.
/learn https://web.dev/learn/html/semantic-html

5.
/learn https://web.dev/learn/css/selectors

6.
/learn https://web.dev/learn/accessibility/why

7.
/learn https://docs.python.org/3/tutorial/controlflow.html

8.
/learn https://docs.python.org/3/tutorial/datastructures.html

9.
/learn https://www.postgresql.org/docs/current/tutorial-select.html

10.
/learn https://www.postgresql.org/docs/current/tutorial-join.html

11.
/learn https://react.dev/learn/state-a-components-memory

12.
/learn https://react.dev/learn/passing-props-to-a-component

For each /learn result, record:
- Did the bot reply?
- Was the summary specific to the URL?
- Did it include difficulty?
- Did it include key points?
- Did it include main concepts?
- Did the Start quiz button appear?
- Any obvious formatting or content problems?

Negative /learn test:
Send:
/learn

Record whether usage guidance appears.

Topic picker and pagination test:
Send:
/quiz

Record:
- Whether saved topic buttons appear.
- Whether multiple different topics appear.
- Whether duplicate topics are suppressed or reduced.
- Whether newest topics appear first.
- Whether pagination buttons appear, such as Older topics / Newer topics.
- Whether pressing Older topics shows another page.
- Whether pressing Newer topics returns to the newer page.
- Do not click any Telegram UI outside the bot chat.

Quiz flow test:
Choose one topic from the topic picker.

Record:
- Whether Question 1 of 5 appears.
- Whether the question is specific to the selected topic.
- Whether A/B/C/D inline answer buttons appear.

Complete the quiz by pressing one answer per question.

Record:
- Whether each answer advances to the next question.
- Whether there are exactly five questions.
- Whether final score percentage appears.
- Whether per-question feedback appears.
- Whether incorrect answers include explanations.

Optional second quiz:
If the first quiz works, run one more quiz from a different topic category, for example one web topic and one Python/PostgreSQL/React topic. Do not complete more than two quizzes total.

Persistence / no restart test:
After finishing a quiz, send:
/quiz

Record whether saved topics still appear without any manual restart.

Fallback test:
Send:
hello

Record whether the bot gives a useful fallback message.

Report format:
Return a concise test report with:
- Overall pass/fail.
- Links tested and status for each.
- /quiz topic picker and pagination observations.
- Quiz completion observations.
- Defects, confusing behavior, or flaky steps.
- Screenshots only if they show the @AskBrAInyBot chat and no unrelated chats, contacts, groups, or personal information.
- Do not include tokens, secrets, personal account details, or unrelated Telegram UI.

Stop conditions:
- If current chat is not @AskBrAInyBot, stop.
- If a click would interact with another chat/channel/contact, stop.
- If Telegram Web exposes personal chats in a way that must be inspected to proceed, stop and ask me to navigate manually.
- If three /learn links fail consecutively, stop the batch and report the failures.
```
