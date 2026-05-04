# Task 2 Technical Report

## Overview

GatherPass is a Lovable-generated seeded demo application for running free community events end to end. It covers public event discovery, Host publishing, RSVP capacity handling, FIFO waitlists, QR tickets, manual check-in, CSV export, post-event feedback, gallery approval, and reporting.

The submission was optimized for deterministic review. A reviewer can open the deployed app, reset demo data, switch between seeded accounts, and exercise the full Publish -> RSVP -> Ticket -> Check-in flow without creating a database, connecting payments, configuring real authentication, or relying on external services.

Deployment: https://gather-event-joy.lovable.app

## Submission Artifact Status

The `task.md` submission-artifact checklist is covered as follows:

| Required artifact | Status | Notes |
|-------------------|--------|-------|
| Shareable public deployed application URL | Done | The Lovable deployment is available at https://gather-event-joy.lovable.app |
| Seeded Host, upcoming event, and past event | Done | Brightside Collective, Sunset Sketch Walk, and Spring Picnic Potluck are included in the resettable seed data |
| Example CSV export file with correct schema | Done | `task-2/example-rsvp-export.csv` demonstrates `name,email,RSVP status,check-in time` |
| `report.md` covering tools, techniques, what worked, what did not, and notable decisions | Done | This report documents the implementation approach, AI toolchain, QA process, failures, and decisions |
| Step-by-step README usage guide for Publish -> RSVP -> Ticket -> Check-in | Done | `task-2/README.md` contains the reviewer-facing usage guide |
| Public GitHub repository with the project in `task-2/` | Ready for final visibility check | The local remote points to `Gennady-Andreyev/Vention-AI-Challenge-2.0`; confirm the GitHub repository is public before final submission |

## Technical Approach

The solution uses a client-side seeded demo architecture. Lovable generated the application code and deployment, while the repository documents the prompting, QA strategy, and submission artifacts.

Core technical choices:

- Runtime state is backed by `localStorage`, with a Reset demo data action restoring the canonical seed.
- Authentication is represented by local demo email/password sign-in plus Create Account, rather than production auth.
- Role behavior is modeled through seeded Host and Checker memberships.
- Event visibility is modeled with Draft/Published and Public/Unlisted fields.
- RSVP state is modeled as Going, Waitlisted, and Cancelled.
- Waitlist promotion is FIFO and triggered by Going cancellation and capacity increases.
- Tickets use unique ticket codes and QR renderings; check-in accepts manual code entry.
- CSV export is generated client-side with the required schema.
- Calendar export downloads an `.ics` file from the browser.
- Feedback, gallery photos, reports, and moderation queues are represented in the same seeded client state.

This architecture is intentionally not a production backend architecture. It is a challenge-review architecture: deterministic, resettable, and directly inspectable by reviewers.

## AI Toolchain and Prompt Engineering

Lovable was the primary implementation environment. It generated and deployed the GatherPass app from structured prompts.

OpenAI Codex was used to produce the Lovable prompts, QA prompts, and repository submission artifacts. Codex was used with the GPT-5.5 model and an extra-high reasoning/intelligence configuration for the planning and documentation work. The workflow used two collaboration modes:

- Plan Mode for requirements decomposition, prompt sequencing, architecture decisions, and QA plan design.
- Default Mode for writing repository artifacts after the plan was approved.

Codex was used for:

- Extracting the requirement surface from `task.md`.
- Converting the task into phased Lovable prompts.
- Designing acceptance tests for each Lovable phase.
- Creating Claude browser-extension and OpenAI Atlas QA prompts.
- Drafting and maintaining the repository documentation and CSV artifact.

The Claude browser extension was used as the first independent UI test driver. Instead of treating Lovable's own implementation summary as sufficient proof, the Claude extension was given a structured QA brief and asked to operate the deployed app through the browser. This made the test process closer to an organizer or reviewer exercising the submission manually.

The Claude-driven UI testing covered:

- Navigating the deployed app as signed-out user, Attendee, Host, and Checker.
- Resetting seeded localStorage data before destructive flows.
- Executing the golden path from Explore to RSVP, ticket creation, manual check-in, duplicate rejection, and undo.
- Verifying route guards and role-specific navigation through the visible UI.
- Checking stateful edge cases such as Draft direct URLs, waitlist promotion, Event Editor validation, gallery approval, and report moderation.
- Producing concise Lovable bug-fix prompts when behavior failed acceptance criteria.

OpenAI Atlas was then added alongside Claude as a second browser-based QA driver for the updated all-round test pass, with extra focus on the corrected authentication experience: visible email/password sign-in, Create Account, seeded-user credentials, redirect preservation, and removal of primary mock-account shortcuts.

This split responsibilities cleanly: Codex produced the requirements-aware prompts and test plans, Lovable implemented the app, Claude extension performed the first independent browser QA pass, and Atlas was used for the follow-up all-round UI validation.

The main prompt-engineering decision was to avoid one huge implementation prompt. The final prompt pack starts with a stage-setting brief, then asks Lovable to build in phases:

1. Public discovery, RSVP, tickets, and waitlist.
2. Host registration, event editor, dashboard, and CSV export.
3. Roles, invites, My Events, and check-in.
4. Feedback, gallery approval, reporting, and moderation.
5. Final requirement-by-requirement hardening.

Each phase included explicit acceptance tests. This made later Lovable iterations more targeted and reduced the risk of visually complete but behaviorally shallow pages.

## Application Design Details

### Data and State

The app maintains seeded users, Hosts, memberships, events, RSVPs, tickets, check-ins, feedback, gallery photos, and reports in local browser state. Reset demo data restores the seeded state used by the QA plan.

Seeded accounts cover the main permission and state combinations:

- Maya Chen: attendee.
- Jordan Lee: Host of Brightside Collective.
- Alex Rivera: Checker for Brightside Collective.
- Priya Shah: waitlisted attendee.
- Omar Brooks: attendee on the full event.
- Riley Morgan: waitlisted/edge-case attendee.

Seeded events cover the required visibility and lifecycle states:

- Upcoming open event.
- Upcoming full event with waitlist.
- Past event.
- Draft event.
- Unlisted event.

### RSVP and Waitlist

RSVP capacity is enforced client-side. If Going count is below capacity, the attendee receives a Going RSVP and ticket. If the event is full, the attendee enters the waitlist. Promotion is FIFO based on waitlist creation order.

Promotion paths tested:

- A Going attendee cancels.
- A Host increases capacity on a full event.

### Ticketing and Check-In

Confirmed attendees receive a unique ticket code and QR display. The challenge does not require camera scanning, so the implemented check-in flow uses manual ticket-code entry. The check-in page validates:

- Valid Going ticket.
- Duplicate ticket.
- Invalid ticket code.
- Waitlisted ticket.
- Cancelled ticket.

It also supports undoing the last successful scan and updates live counters.

### Roles and Permissions

The app models Host and Checker roles per Host.

- Host can create and manage events, view dashboard data, export CSVs, approve gallery uploads, and review reports.
- Checker can access check-in for events under the Host and does not receive Host management actions.
- Signed-out users and attendees are redirected away from protected routes.

Draft direct URLs are guarded so only the owning Host can preview or manage draft content.

### Community and Moderation

Past events expose feedback and gallery actions. Feedback requires a 1-5 rating and accepts an optional comment. Gallery uploads enter Pending state, and only approved photos are public. Reports appear in a Host review queue where the Host can resolve reports or hide reported content.

## What Worked

Phased prompting worked well. It gave Lovable smaller state machines to implement and made each iteration reviewable against concrete acceptance tests.

The seeded localStorage approach worked well for deterministic challenge review. Reset demo data made it possible to repeat destructive flows such as check-in, undo, waitlist promotion, and moderation without external setup.

The independent Claude browser-extension QA pass was valuable. It tested through the deployed UI and caught issues that a code-level self-check could miss, including draft event access and missing event-editor validation feedback.

## What Did Not Work

The initial instinct to create a single large Lovable build prompt was rejected. The feature surface is too wide and stateful for one implementation pass.

Some browser-preview constraints limited direct inspection of social metadata and `.ics` file contents from inside an iframe. Those areas were verified through a mix of browser behavior, Lovable code review, and targeted follow-up checks.

A route-based QA blind spot emerged during later review. AI-driven browser tests could validate Host Dashboard and event-editor behavior by navigating directly to known routes, but that did not prove a real user could discover those flows from the visible UI. In one pass, the Host functionality existed behind routes, while a signed-in non-host user had no obvious navigation affordance to begin Host registration. This made a feature appear implemented under automated route-based QA while remaining effectively unavailable to an ordinary user. The test scenario was updated to require visible navigation discovery before direct-route checks for protected and role-based flows.

Real camera scanning was not implemented. The task explicitly states that manual code entry is sufficient, so the implementation focuses on generated QR tickets and robust manual validation.

## Notable Decisions

- Use localStorage instead of Supabase or another backend to keep review setup friction at zero.
- Make Explore the first useful screen, rather than a landing page.
- Keep Paid visible but disabled with a "Coming soon" tooltip.
- Treat Draft event direct URLs as protected Host-only previews.
- Use manual code entry for check-in, while still generating QR tickets.
- Keep repository artifacts separate from the Lovable app generation prompts.
- Use Claude browser-extension QA as an independent black-box pass after Lovable self-checks, then add Atlas for a follow-up all-round UI test after auth changes.

## QA Summary

Testing used three layers:

- Lovable self-checks after implementation and hardening.
- Independent browser QA with a Claude extension using the requirement-mapped scenario plan.
- Follow-up all-round browser QA with OpenAI Atlas, focused especially on the updated email/password and Create Account flows.
- Targeted cross-testing for final risk areas: draft route guards, editor validation, FIFO promotion, invite links, page metadata, and `.ics` export.

The final detailed results are documented in [final-test-report.md](final-test-report.md).

## Deployment

Public URL: https://gather-event-joy.lovable.app

## Remaining Limitations

- Demo persistence is browser-local and resettable by design.
- QR camera scanning is not included; manual ticket-code entry is the supported check-in method.
- Paid events are intentionally disabled.
- The seeded dataset includes one Host, though the role model supports adding more via demo flows.
