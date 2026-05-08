# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Purpose

Personal submissions for the Vention AI Challenge 2.0 by Gennady Andreyev.

## Structure

Each top-level `task-N/` directory is an independent submission for one challenge task. The directories start empty (`.gitkeep` only) and will grow as tasks are completed.

| Directory | Description |
|-----------|-------------|
| [task-1/](task-1/) | Task 1 submission |
| [task-2/](task-2/) | Task 2 submission |
| [task-3/](task-3/) | Task 3 submission |
| [task-4/](task-4/) | Task 4 submission |

## Development notes

- Tasks are independent — each `task-N/` directory has its own stack, dependencies, and tooling. Navigate into the relevant directory before running any build/test/lint commands.
- Update the README.md table (mark the `Done` checkbox and fill in the submission date) when a task is completed.

## Report writing style

When creating or updating task reports, write them as an honest author-centered implementation narrative, not as a generic product or vendor summary.

- Prefer a moderately formal tone.
- Avoid first-person singular phrasing like "I did"; describe the work in neutral author-centered language such as "the migration used", "the workflow was", "the author steered", or "Codex was used".
- Make the report explain the actual path taken: planning, prompting, implementation loop, testing loop, gotchas, corrections, and final state.
- Explicitly distinguish the roles of the tools:
  - Codex: planning, prompt generation, test-plan generation, analysis of Lovable/Atlas outputs, and report drafting.
  - Lovable or other builder tools: implementation work, generated code, backend/schema/RLS work, UI changes, and deployment.
  - Atlas, Claude, or browser test drivers: independent UI validation and evidence gathering.
- Be candid about tool limitations and failures. If Lovable or another LLM did the heavy implementation work, say so. If a tool summary was not enough proof and browser testing found issues, say so.
- Include sections for what worked, what did not work, and notable gotchas. Focus these sections on the author's real workflow and decisions, not only on app features.
- Keep technical implementation details, but place them in service of the story: why a choice was made, what broke, how it was diagnosed, and how it was fixed.
- When a follow-up implementation extends an earlier solution, preserve that chronology instead of rewriting history as if the final architecture was chosen from the start.
