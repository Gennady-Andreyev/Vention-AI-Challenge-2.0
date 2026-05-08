# Task 2 Technical Report

## Overview

GatherPass is a Lovable Cloud application for running free community events end to end. It covers public event discovery, Host publishing, RSVP capacity handling, FIFO waitlists, QR tickets, manual check-in, CSV export, post-event feedback, gallery approval, reporting, and role-based Host/Checker workflows.

Official deployment: https://gather-pass-hub.lovable.app/

The current submission is the stateful version. Users, hosts, events, RSVPs, tickets, check-ins, invites, feedback, gallery photos, and reports are stored in Lovable Cloud so changes made by one user/session are visible to other users/sessions. The development path, however, started with a browser-state prototype and then evolved into this backend-backed version.

## Submission Artifact Status

| Required artifact | Status | Notes |
|-------------------|--------|-------|
| Shareable public deployed application URL | Done | https://gather-pass-hub.lovable.app/ |
| Seeded Host, upcoming event, and past event | Done | Brightside Collective, Sunset Sketch Walk, and Spring Picnic Potluck are included in the Cloud seed data |
| Example CSV export file with correct schema | Done | `task-2/example-rsvp-export.csv` demonstrates `name,email,RSVP status,check-in time` |
| `report.md` covering tools, techniques, what worked, what did not, and notable decisions | Done | This report documents the implementation approach, AI toolchain, QA process, failures, and decisions |
| Step-by-step README usage guide for Publish -> RSVP -> Ticket -> Check-in | Done | `task-2/README.md` contains the reviewer-facing usage guide |
| Public GitHub repository with the project in `task-2/` | Done | https://github.com/Gennady-Andreyev/Vention-AI-Challenge-2.0/tree/main/task-2 |

## Technical Approach

The implementation approach had two stages. First, Lovable was used to create a complete browser-state prototype that covered the whole product surface quickly. Then that working app was remixed and migrated to Lovable Cloud, preserving the UI and route structure while replacing local application state with shared backend persistence.

The final implementation uses Lovable Cloud as the backend layer while preserving the application experience created in Lovable. The UI remains a practical event-operations tool with Explore, event pages, Host Dashboard, Event Editor, My Tickets, My Events, check-in, invites, feedback, gallery, and report moderation.

Core technical choices:

- Lovable Cloud Auth is used for email/password sign-in and seeded review accounts.
- Shared application data is stored in Cloud tables: `profiles`, `public_profiles`, `hosts`, `host_members`, `events`, `rsvps`, `tickets`, `check_ins`, `invites`, `feedback`, `gallery_photos`, and `reports`.
- Row-level security separates public browsing, attendee-owned data, Host access, Checker access, owner-only tickets, and moderation queues.
- RSVP capacity, ticket issuance, cancel-and-promote, capacity promotion, check-in, undo check-in, invite creation, invite acceptance, and Host registration use backend RPCs where permission or race-safety matters.
- Simpler writes such as event metadata, feedback, gallery metadata, and report creation use direct Cloud writes protected by RLS.
- Gallery uploads use a Cloud storage bucket with public display controlled by `gallery_photos.status`.
- A public reset action is intentionally absent because the app now uses shared backend state.
- CSV export keeps the required schema: `name,email,RSVP status,check-in time`.
- Calendar export and QR rendering remain browser-side features.

## Initial Browser-State Prototype

The first implementation goal was to make the entire challenge surface usable in Lovable with minimal setup. Codex helped turn `task.md` into a phased Lovable prompt pack, and Lovable generated a seeded app that could be reviewed immediately through the browser.

That first prototype used seeded accounts, seeded events, and browser-scoped state. It included the key roles and flows: Attendee, Host, Checker, Explore, Event detail, RSVP, waitlist, QR ticket, My Tickets, Host Dashboard, Event Editor, CSV export, invites, My Events, check-in, feedback, gallery moderation, and reports.

The prototype was intentionally built in phases:

1. Public discovery, RSVP, tickets, and waitlist.
2. Host registration, event editor, dashboard, and CSV export.
3. Roles, invites, My Events, and check-in.
4. Feedback, gallery approval, reporting, and moderation.
5. Final requirement-by-requirement hardening.

This was useful because it turned a large task into smaller state machines that could be reviewed one at a time. It also exposed the shape of the product before backend complexity was introduced.

The first independent browser testing used a Claude browser extension and later OpenAI Atlas. This testing found issues that Lovable's own summaries did not prove, including draft route access, missing Event Editor validation, discoverability gaps for Host registration/member management, and security issues around ticket privacy and reusable invites. Those issues were fixed before the backend migration became the next step.

## Evolution From Browser State To Cloud State

The project first reached a working state as a browser-state prototype. That version was useful for fast deterministic review and for proving the product flows, but it was not enough once the task moved toward shared multi-user behavior. Events, RSVPs, tickets, and role changes created in one browser session needed to be visible to other users and sessions.

The conversion was therefore handled as an extension of the existing app rather than a rebuild. A Lovable remix was created, the current UI/routes/flows were preserved, and the state/auth layer was migrated to Lovable Cloud. This kept the working product surface intact while replacing the persistence model underneath it.

The migration path was staged:

- Inspect the existing state/auth layer and identify where pages consumed shared state.
- Add Lovable Cloud schema, auth, RLS, storage, and seeded data.
- Replace prototype auth and reads with Cloud-backed auth and reads.
- Move RSVP, tickets, and waitlist behavior into transaction-safe backend RPCs.
- Move Host writes, event editor writes, check-in, invites, feedback, gallery, and reports to Cloud.
- Harden RLS/function grants and run Lovable security checks.
- Use OpenAI Atlas browser tests after each meaningful phase.

This phased approach mattered because the app contains several interacting state machines: RSVP capacity, FIFO waitlists, tickets, check-in, role membership, invites, gallery moderation, and reports. Testing one backend surface at a time made failures much easier to isolate.

## AI Toolchain And Prompting

Lovable was the primary implementation environment. Its LLM performed most of the code-generation work: first the product prototype, then the schema creation, RLS setup, RPC implementation, frontend rewiring, and UI-preserving backend migration.

OpenAI Codex was used as the planning, prompting, and analysis layer. Codex produced the initial Lovable product prompts, the Cloud migration prompts, Claude/Atlas QA prompts, and repository documentation, then converted Lovable/Atlas outputs into smaller follow-up prompts when failures appeared. Codex was especially useful for turning broad product/backend goals into narrower implementation phases.

The Claude browser extension was used as the first independent UI test driver for the prototype. OpenAI Atlas then became the main independent UI test driver for the stateful version. Tests were written to prefer visible navigation first, then direct route/security checks. This caught issues that Lovable summaries alone did not prove.

The practical loop became:

1. Codex drafts a focused Lovable prompt.
2. Lovable implements the phase.
3. Atlas tests the app through the browser.
4. Codex analyzes the failure report and drafts a smaller corrective prompt.
5. The cycle repeats only for confirmed blockers.

This was also important for Lovable credit usage. Broad retry prompts were avoided once Atlas could identify concrete failing flows.

## Application Design Details

### Data And Auth

Cloud auth provides the seeded review accounts:

- Maya Chen: attendee.
- Jordan Lee: Host of Brightside Collective.
- Alex Rivera: Checker for Brightside Collective.
- Priya Shah: attendee/waitlist checks.
- Omar Hassan: attendee/RSVP checks.
- Riley Morgan: attendee/invite and edge-case checks.

Private profile data lives in `profiles`; public-safe display data lives in `public_profiles`. Host membership is stored in `host_members`, not on user profile rows, so Host/Checker permissions remain scoped to a Host organization.

### RSVP, Tickets, And Waitlist

RSVPs are backend-backed. The `rsvp_to_event` RPC locks the event row, checks capacity, creates or updates the RSVP, and issues a ticket when the attendee is Going. If the event is full, the attendee is Waitlisted and receives no confirmed ticket.

`cancel_rsvp`, `promote_waitlist`, and `update_event_capacity` keep promotion FIFO. Confirmed tickets are owner-only, and waitlisted/cancelled attendees cannot access confirmed ticket pages.

### Host, Checker, And Check-In

Hosts can create and manage events, publish/unpublish, duplicate, export CSV, create invites, approve/hide gallery photos, and moderate reports. Checkers can access check-in for events under their Host but do not receive Host management actions.

Check-in uses backend validation through `check_in_ticket`. It accepts valid Going ticket codes, blocks duplicate scans, rejects invalid/wrong-event/non-confirmed codes, records who checked the attendee in, and supports undo via `undo_check_in`.

### Community And Moderation

Past events expose feedback and gallery actions. Feedback requires a 1-5 rating and an authenticated attendee. Gallery uploads start Pending and must be approved before public display. Reports are stored in Cloud and appear in the relevant Host review queue.

## Migration Gotchas

The migration surfaced several concrete issues.

Auth initialization initially treated "session still loading" as "signed out," so refreshes on protected routes redirected to sign-in. The fix was to introduce explicit auth readiness/loading behavior and delay route decisions until the Cloud session resolved.

Role-derived navigation could briefly remain stale after account switching. The fix was to clear user-scoped state on sign-out and refetch memberships immediately after sign-in.

The RSVP RPC contained a PostgreSQL `FOUND` bug. An aggregate count query overwrote the implicit `FOUND` value from the earlier RSVP lookup, so first-time RSVPs could go down an update path with no row to update. Atlas exposed this because under-capacity RSVP failed while some waitlist paths appeared to work.

Ticket generation also failed because `_gen_ticket_code` used `gen_random_bytes`, which was not available in the deployed database context. Under-capacity RSVP hit ticket generation and failed; full-event waitlist RSVP skipped ticket issuance and therefore passed. The ticket code generator was changed to derive randomness from `gen_random_uuid`.

The Event Editor needed hardening after Atlas found date/time input state, capacity editing, and cover URL editing could prevent valid draft creation. Fixing those inputs made draft creation, publish/unpublish, and duplicate persistence reliable.

The Create Account flow produced a late auth issue that was not caught by the earlier LLM-backed testing. Most automated auth checks used seeded accounts, so the first-time user path was under-tested. A manual exploratory check found that several unique emails were incorrectly rejected with "account already exists." After a targeted Lovable fix, Atlas retested account creation with `atlas-create-20260508-213000@example.com`: the account was created without email verification, the session persisted after refresh, RSVP/ticket creation worked, duplicate email was rejected accurately, and invalid email/short password errors were correctly distinguished.

Lovable's security scan found backend hardening work that browser happy-path tests did not prove. Feedback comments were no longer made publicly readable, invite token lookup stayed behind backend acceptance, mutation RPCs were restricted to authenticated callers, and internal helper functions had public execution revoked.

## What Worked

Using Codex as a planning and review partner worked well. Codex did much of the heavy lifting in turning the backend idea into phased Lovable prompts, narrowing failed test results into targeted fix prompts, and producing Atlas test scenarios. This reduced the amount of manual backend design and prompt-writing required.

The browser-state prototype worked well as a first step. It made the full product surface visible and testable before backend complexity entered the picture. That made the later migration easier because the desired UI and behavior were already concrete.

Using Lovable for implementation worked well once the prompts became specific. Lovable's LLM handled most of the prototype implementation, schema creation, RLS setup, RPC implementation, frontend rewiring, and UI-preserving migration work. The author's role was mainly to steer scope, paste prompts, run the app, review outputs, and decide which failures mattered.

Atlas was useful as the independent checker. Running the app through Atlas made it clear which Lovable claims were actually true in the browser. This was especially useful for auth refresh, role navigation, RSVP persistence, Event Editor validation, and final end-to-end checks.

## What Did Not Work

Broad prompts and broad test passes did not work well. When too much was tested or requested at once, one early failure blocked the rest of the validation. The work became more effective after narrowing each loop to one surface area: auth, RSVP, Event Editor, remaining writes, then security hardening.

Lovable's implementation summaries could not be treated as proof. Several flows were reported as implemented before browser testing showed they were broken or incomplete.

The prototype stage also exposed a recurring route-discoverability problem. Some functionality existed by direct URL or internal state path, but a real user could not find it through visible navigation. This affected Host registration and Host member/invite management during earlier QA. The test scenarios were adjusted to require visible navigation before direct route checks.

The Create Account issue showed another blind spot: seeded-user testing can make auth look healthier than it is. LLM-backed browser testing repeatedly exercised known users, while manual checking of a genuinely new account uncovered the broken signup path. The final test plan now keeps a dedicated timestamped-email Create Account scenario with duplicate and invalid-input probes.

The initial browser-state implementation also had security weaknesses that happy-path UI testing did not catch. In particular, ticket pages needed owner-only access, and Host invite links needed expiry/single-use behavior. Lovable's security scan and targeted follow-up prompts were useful for catching and fixing those gaps.

Codex was helpful at planning and diagnosis, but it could not directly inspect or operate the Lovable editor. The author still had to act as the bridge: paste prompts into Lovable, run Atlas sessions, collect screenshots/results, and bring outputs back for analysis.

Lovable's LLM also made subtle backend mistakes. It implemented much of the backend successfully, but issues such as the PostgreSQL `FOUND` flag bug, unavailable `gen_random_bytes`, auth refresh timing, stale role navigation, and fragile Event Editor validation surfaced only through testing.

Real camera scanning was not implemented. The task explicitly states that manual code entry is sufficient, so the implementation focuses on generated QR tickets and robust manual validation.

## Notable Decisions

- Promote the Lovable Cloud remix as the official Task 2 submission.
- Keep the browser-state prototype in the development record as the first working version, but not as the final submission target.
- Preserve the existing UI and routes while migrating persistence underneath.
- Use Lovable Cloud only, with no custom backend server or external Supabase project.
- Move race-sensitive operations to backend RPCs.
- Remove public reset because shared backend reset would affect all users/sessions.
- Keep Paid visible but disabled with a "Coming soon" tooltip.
- Use manual code entry for check-in while still generating QR tickets.
- Use Atlas before spending additional Lovable credits, then send Lovable narrow fix prompts only for confirmed blockers.

## QA Summary

Testing used four layers:

- Lovable self-checks after implementation phases.
- OpenAI Atlas browser QA after meaningful migration phases.
- Lovable internal security scan for RLS/function-grant issues.
- Manual exploratory checks for gaps not covered by seeded-account LLM testing, including true first-time account creation.
- Targeted regression checks after confirmed blockers.

The final Atlas pass found no blocking issues. It verified public browsing, unlisted and draft behavior, RSVP/ticket/waitlist flows, owner-only tickets, Host event writes, capacity promotion, check-in and undo, single-use invites, feedback, gallery moderation, report moderation, role boundaries, absence of public reset, and absence of browser-local persistence messaging.

Detailed final results are documented in [final-test-report.md](final-test-report.md).

## Deployment

Official public URL: https://gather-pass-hub.lovable.app/

## Remaining Limitations

- QR camera scanning is not included; manual ticket-code entry is the supported check-in method.
- Paid events are intentionally disabled.
- The seeded dataset includes one Host, though the role model supports additional Hosts.
- Atlas could trigger CSV download but could not inspect downloaded file contents in every environment; the repository includes [example-rsvp-export.csv](example-rsvp-export.csv) with the required schema.
