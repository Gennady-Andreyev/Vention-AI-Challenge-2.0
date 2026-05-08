# GatherPass Lovable Prompt History

This file preserves the full Lovable prompting path for Task 2. The official deployed submission is the stateful Lovable Cloud app at https://gather-pass-hub.lovable.app/.

The work happened in two major stages:

1. A browser-state prototype was built first to make the full product surface reviewable quickly.
2. That working app was then remixed and migrated to Lovable Cloud so users, events, RSVPs, tickets, check-ins, invites, feedback, gallery items, and reports became shared across sessions.

## Part 1: Browser-State Prototype Prompt Pack

The prompts below created the initial working GatherPass prototype. They are retained as development history, not as the current submission target.

### Original Prototype Pack Intro

Use these prompts in order inside Lovable. The goal is to build GatherPass as a complete, seeded, reviewable demo app with minimal rework.

Locked decisions:

- Product name: GatherPass.
- Architecture: localStorage-backed seeded demo with demo sign-in/account switching.
- No Supabase, external auth, payments, backend services, or manual database setup.
- Seed theme: generic community events.
- Lovable should build the deployed app only. Repository artifacts such as `README.md`, `report.md`, and a sample CSV file will be created separately later.
- UI style: practical event operations tool, not a marketing landing page.

## Prompt 0: Stage-Setting Session Brief

Paste this first. It should set context and get Lovable aligned before implementation begins.

```text
We are building GatherPass, a challenge submission app for free community event hosting, RSVP tickets, waitlists, host operations, venue check-in, feedback, gallery approval, and reporting.

Use a seeded demo architecture with localStorage persistence and demo sign-in/account switching. Do not use Supabase, external auth, payments, backend services, or manual database setup. The deployed app must be fully reviewable with seeded data and no setup.

This app should feel like a practical operations tool, not a marketing landing page. The first useful screen should be Explore events. Use generic community event seed data.

We will build this in phases:
1. App foundation, public discovery, RSVP, tickets, and waitlist.
2. Host registration, event editor, dashboard, and CSV export.
3. Roles, invite links, My Events, and checker check-in.
4. Feedback, gallery approval, reporting, and moderation.
5. Final QA hardening.

For now, do not implement yet. Confirm the proposed route map, data entities, demo accounts, seeded data, and phased build approach. Keep the plan concise and flag any risks before we start.
```

## Prompt 1: App Foundation and Public RSVP Flow

Use this after Lovable confirms Prompt 0.

```text
Now implement Phase 1 for GatherPass.

Keep the agreed architecture and UI direction:
- React/Vite-style Lovable app.
- localStorage-backed seeded demo state.
- Demo sign-in/account switching.
- No Supabase, backend, external auth, payment setup, or manual database setup.
- Do not create repository README.md, report.md, or sample CSV artifacts. Those will be handled later outside Lovable.
- Build real working routes and state transitions, not placeholder screens.

Product goal:
GatherPass helps organizers publish free community events, attendees RSVP and receive digital tickets, and checkers validate tickets at the venue. In this phase, build the public discovery, event detail, RSVP, ticket, and waitlist foundations.

Demo accounts:
- Attendee: Maya Chen, maya@example.com
- Host: Jordan Lee, jordan@example.com
- Checker: Alex Rivera, alex@example.com
- Extra attendee for waitlist testing: Priya Shah, priya@example.com
- Extra attendee for promotion testing: Omar Brooks, omar@example.com
- Extra attendee for cancellation/testing edge cases: Riley Morgan, riley@example.com
- The demo sign-in/account switcher should expose all seeded users so every RSVP, waitlist, promotion, check-in, and moderation scenario is directly testable.

Seed data:
- One Host profile with name, logo/avatar, short bio, contact email, and public Host page.
- One upcoming published public event with remaining capacity.
- One upcoming published public event that is already at capacity with at least one waitlisted attendee.
- One past published public event.
- One draft event for host management.
- One unlisted published event that is reachable by direct link but hidden from Explore.
- Include existing RSVPs, waitlist records, tickets, and at least one check-in so counters have realistic data.
- Use the extra attendee accounts to seed at least one Going RSVP, one Waitlisted RSVP, one Cancelled RSVP, one unchecked ticket, and one already checked-in ticket.

Core entities to model in local state:
- User: id, name, email.
- Host profile: id, name, logo/avatar, short bio, contact email.
- Host member: hostId, userId, role where role is Host or Checker.
- Event: id, hostId, title, description, start date/time, end date/time, timezone, venue address or online link, capacity, cover image, visibility Public/Unlisted, status Draft/Published, pricing Free.
- RSVP: eventId, userId, status Going/Waitlisted/Cancelled, createdAt, promotedAt.
- Ticket: eventId, userId, unique ticket code, QR code payload.
- Check-in: eventId, ticketCode, userId, checkedInAt, checkedInBy.

Required navigation:
- Explore
- My Tickets
- My Events
- Host Dashboard
- Sign In / Profile
- Reset demo data action

Routes to implement in this phase:
1. Explore page
   - Make this the first useful screen.
   - Browse published public events.
   - Upcoming is the default filter.
   - Include text search, date range filter, location filter, and Include Past toggle.
   - Past events show a clear Ended state.
   - RSVP action is hidden for past events.
   - Draft events never appear.
   - Unlisted events never appear.

2. Event detail page
   - Show title, cover image, host, description, start/end time with timezone, venue/online link, capacity, Going count, Waitlist count, and Ended state when applicable.
   - Public events are reachable from Explore.
   - Unlisted published events work by direct link only.
   - Set meaningful document title and meta description for shareable links.
   - Past events hide RSVP and show Ended.
   - Upcoming events show RSVP or current attendee status.

3. Sign-in flow
   - Use demo account switching, not real auth.
   - Signed-out users can browse Explore and event pages.
   - If a signed-out user clicks RSVP, route them to Sign In and return them to the same event page after sign-in.

4. RSVP and waitlist
   - Signed-in users can RSVP to upcoming published events.
   - If capacity is available, create a Going RSVP and a unique ticket immediately.
   - If capacity is full, create a Waitlisted RSVP.
   - Attendees can cancel their RSVP.
   - If a Going attendee cancels, automatically promote the oldest Waitlisted attendee FIFO and set promotedAt.
   - Show a visible in-app promotion notice to an attendee who was promoted from waitlist.

5. Ticket display and My Tickets
   - Confirmed attendees can view a ticket with unique code and QR code.
   - The QR code payload should include the ticket code.
   - Add to Calendar downloads a valid .ics file with title, start/end, timezone, and location/link.
   - My Tickets shows upcoming confirmed tickets.
   - My Tickets shows upcoming waitlisted events separately with a clear waitlist state.

Acceptance tests Lovable must satisfy before stopping:
- Signed-out user can browse Explore and event detail pages.
- Signed-out user clicking RSVP goes to Sign In and returns to the original event after sign-in.
- RSVP under capacity creates Going status and a ticket with QR code.
- RSVP at capacity creates Waitlisted status.
- Canceling a Going RSVP promotes the oldest waitlisted attendee.
- Past event pages show Ended and hide RSVP.
- Draft and unlisted events do not appear in Explore.
- Unlisted event works by direct URL.
- My Tickets shows confirmed tickets and waitlisted events separately.
- Add to Calendar downloads a valid .ics file.
- Refreshing the page preserves state; Reset demo data restores the seed.

After implementing, summarize only the routes built, demo accounts, and any known gaps for later phases.
```

## Prompt 2: Host Operations and Event Editor

Use this after Phase 1 works.

```text
Implement Phase 2 for GatherPass: Host registration, event editor, Host Dashboard, and CSV export.

Keep the existing architecture and UI direction. Do not redesign unrelated screens, replace the data model, introduce Supabase/backend services, or create repository README/report/sample CSV files. Extend the current localStorage demo state and route structure.

Required Host capabilities:
- A signed-in user can register as a Host.
- Host profile fields: name, logo/avatar, short bio, contact email.
- After registration, the current user has Host role for that Host.
- Host profile has a public Host page showing host details and published events.
- Host pages set meaningful document title and meta description.

Event editor:
- Host can create and edit events for their Host.
- Required fields: title, description, start date/time, end date/time, timezone, venue address or online link, capacity, cover image, visibility Public/Unlisted, status Draft/Published.
- Add validation for required fields and sensible date ordering.
- Events can be Draft or Published.
- Events can be Public or Unlisted.
- Include Publish, Unpublish, and Duplicate actions.
- Duplicate creates a new Draft copy with "(Copy)" in the title.
- Free/Paid toggle is visible. Free is selected and works. Paid is disabled with a "Coming soon" tooltip.
- If capacity increases, promote waitlisted attendees FIFO until available capacity is filled.

Host Dashboard:
- Host sees Upcoming and Past event sections.
- Each event row/card shows Going, Waitlist, and Checked-in counts.
- Each event has quick actions: Edit, Duplicate, Publish/Unpublish, Check-in, Export CSV.
- Dashboard includes useful empty states and action feedback.

CSV export:
- Export RSVPs and attendance for an event.
- Download a CSV that opens correctly in spreadsheet apps.
- CSV columns must be exactly: name, email, RSVP status, check-in time.
- Include rows for Going, Waitlisted, Cancelled, and checked-in attendees when available.
- Use blank check-in time when the attendee has not checked in.

Acceptance tests Lovable must satisfy before stopping:
- Signed-in non-host user can register as a Host and edit their Host profile.
- Host can create a draft event, publish it, unpublish it, and duplicate it.
- Public published events appear in Explore; Draft events do not.
- Unlisted published events are hidden from Explore and reachable by direct link.
- Event editor validates required fields and end time after start time.
- Paid option is visible but disabled with "Coming soon" tooltip.
- Increasing capacity promotes waitlisted users FIFO.
- Host Dashboard shows Upcoming/Past events with Going, Waitlist, Checked-in counts.
- Export CSV downloads with exactly these headers: name, email, RSVP status, check-in time.
- Refreshing preserves created/edited events and dashboard state.

After implementing, summarize only what changed and any known gaps for later phases.
```

## Prompt 3: Roles, My Events, and Check-In

Use this after Host operations work.

```text
Implement Phase 3 for GatherPass: Host/Checker roles, invite links, My Events, and event check-in.

Keep the existing architecture and UI direction. Do not redesign unrelated screens, replace the data model, introduce Supabase/backend services, or create repository README/report/sample CSV files. Extend the current localStorage demo state and route structure.

Roles and permissions:
- Each Host supports two member roles: Host and Checker.
- Host role can manage events, dashboard, CSV exports, gallery approvals, and reports.
- Checker role is limited to accessing the check-in page for events under that Host.
- Enforce permissions in navigation, visible actions, and route guards.
- Signed-out users should be redirected to Sign In when opening protected routes, then returned afterward.

Member invite links:
- Host can generate/copy invite links for Host and Checker roles.
- Visiting an invite link as a signed-in user assigns that role for the Host.
- Visiting an invite link while signed out sends the user to Sign In, then applies the invite after sign-in.
- Show a clear success message after accepting an invite.
- Prevent duplicate membership records.

My Events page:
- Visible only to users with Host or Checker role.
- Aggregates all events where the current user holds a Host or Checker role.
- Include filters by Host, date range, and text search.
- Host users see management quick actions: Edit, Dashboard, Export CSV, Check-in.
- Checker users see Check-in only.

Check-in page:
- Accessible to Host and Checker roles for that event's Host.
- Manual ticket code entry is sufficient; do not require camera scanning.
- Show live counters: Going, Checked-in, Remaining, Waitlist.
- A valid Going ticket code creates a check-in record.
- Duplicate check-ins are blocked with a clear duplicate message.
- Invalid ticket codes show a clear error.
- Waitlisted or cancelled tickets cannot be checked in.
- Show recent successful scans.
- Support undoing the last successful scan and updating counters.

Seed data:
- Ensure Alex Rivera has Checker role for the seeded Host.
- Ensure there is at least one valid unchecked ticket code visible in seeded data or easy to obtain from My Tickets.
- Ensure there is at least one already checked-in ticket so duplicate prevention can be tested.

Acceptance tests Lovable must satisfy before stopping:
- Host sees Host Dashboard, management actions, and check-in actions.
- Checker sees My Events and check-in actions only.
- Checker cannot edit events, export CSV, or open Host Dashboard management.
- Attendee cannot access My Events, Host Dashboard, or check-in unless invited.
- Host can copy Host and Checker invite links.
- Invite link applies the correct role after sign-in.
- My Events filters by Host, date range, and text search.
- Manual check-in with a valid Going ticket succeeds and updates counters.
- Duplicate check-in is blocked.
- Invalid, Waitlisted, or Cancelled ticket codes are rejected.
- Undo last scan removes the last successful check-in and updates counters.
- Refreshing preserves roles, accepted invites, and check-in state.

After implementing, summarize only what changed and any known gaps for later phases.
```

## Prompt 4: Community Content and Moderation

Use this after roles and check-in work.

```text
Implement Phase 4 for GatherPass: post-event feedback, gallery uploads, approval, reporting, and moderation.

Keep the existing architecture and UI direction. Do not redesign unrelated screens, replace the data model, introduce Supabase/backend services, or create repository README/report/sample CSV files. Extend the current localStorage demo state and route structure.

Add these entities if they are not already present:
- Feedback: eventId, userId, rating 1-5, optional comment, createdAt.
- Gallery photo: eventId, userId, image or image placeholder, caption, status Pending/Approved/Hidden, createdAt.
- Report: target type Event/Photo, targetId, reporterId, reason, status Open/Resolved/Hidden, createdAt.

Post-event feedback:
- Feedback form appears only after an event has ended.
- Feedback requires signed-in user.
- Rating is required and must be 1-5 stars.
- Comment is optional.
- Submitted feedback appears on the event page.
- Prevent obvious duplicate feedback by the same user for the same event, or update the prior feedback cleanly.

Gallery:
- Photo upload appears only after an event has ended and only for signed-in users.
- Since this is a demo, using image URLs, placeholders, or uploaded preview data is acceptable.
- New uploads start as Pending.
- Pending photos are not visible in the public gallery.
- Approved photos appear publicly on the event page.
- Hidden photos do not appear publicly.

Host moderation:
- Host Dashboard includes a gallery approval queue with Approve and Hide actions.
- Host Dashboard includes a report review queue with Resolve and Hide reported item actions.
- Any signed-in user can report an event or a photo with a reason.
- Reported items appear in the Host review queue for that Host.
- Hiding a reported event or photo removes it from public display.
- Management views should show clear Hidden/Open/Resolved/Pending/Approved status labels.

Seed data:
- Add at least one approved gallery photo for the past event.
- Add at least one pending gallery photo.
- Add at least one hidden gallery photo.
- Add at least one submitted feedback item.
- Add at least one open report for an event or photo.

Acceptance tests Lovable must satisfy before stopping:
- Past event shows feedback and gallery actions for signed-in users.
- Upcoming event does not show feedback or gallery upload.
- Signed-out user is prompted to sign in before submitting feedback, upload, or report.
- Feedback requires a 1-5 rating and displays after submission.
- New photo upload starts Pending and is hidden publicly.
- Host can approve a pending photo and it appears publicly.
- Host can hide a photo and it disappears publicly.
- User can report an event and a photo.
- Reports appear in Host review queue.
- Host can resolve a report without hiding the item.
- Host can hide a reported item and it no longer appears publicly.
- Refreshing preserves feedback, gallery, and report state.

After implementing, summarize only what changed and any known gaps for final hardening.
```

## Prompt 5: Final Challenge QA Hardening

Use this near the end, after all feature phases have been implemented.

```text
Run a final requirement-by-requirement QA hardening pass for GatherPass.

Keep the existing architecture and UI direction. Do not redesign unrelated screens, replace the data model, introduce Supabase/backend services, or create repository README/report/sample CSV files. Fix missing behavior rather than merely listing it.

Validate and fix these requirements:
- Unauthenticated users can browse public published events, including past events when Include Past is enabled.
- Explore has text search, date range filter, location filter, Upcoming default, and Include Past toggle.
- Event and Host pages set meaningful document title and meta description.
- Past events clearly show Ended and hide RSVP.
- RSVP while signed out redirects to Sign In and returns to the event page afterward.
- Signed-in users can RSVP, immediately view a unique QR ticket, download Add to Calendar, cancel RSVP, and view tickets on My Tickets.
- Capacity is enforced.
- New RSVPs go to waitlist when capacity is full.
- Waitlist promotion is FIFO after a Going cancellation and after capacity increase.
- Promotion is visible in-app to the affected attendee.
- Signed-in users can register as a Host and manage their Host profile.
- Hosts can create, publish, unpublish, duplicate, and edit Public or Unlisted free events.
- Event editor shows Free/Paid toggle with Paid disabled and a "Coming soon" tooltip.
- Host Dashboard lists Upcoming and Past events with Going, Waitlist, and Checked-in counts.
- CSV export downloads with exactly these headers: name, email, RSVP status, check-in time.
- My Events is visible to Host/Checker users, filters by Host/date/text, and shows role-appropriate actions.
- Checker can open check-in page, enter codes manually, view live counters, avoid duplicate scans, and undo last scan.
- Gallery uploads require Host approval before public display.
- Feedback is available after event ends with 1-5 rating and optional comment.
- Report flow surfaces reported items in a review queue and reported items can be hidden.
- Route guards and navigation enforce Host, Checker, Attendee, and signed-out permissions.
- Seed data includes one Host, one upcoming public event, one past public event, one draft event, one unlisted event, tickets, waitlist, check-ins, feedback, gallery items, and reports.
- Reset demo data restores the original seeded state.
- Refreshing preserves localStorage state.
- Desktop and mobile layouts are usable.
- No route is a placeholder.
- Primary actions have clear success and error feedback.

Final reviewer path that must pass:
1. Reset demo data.
2. Browse Explore while signed out.
3. Open an upcoming event.
4. Click RSVP while signed out.
5. Sign in as Maya Chen and return to the event.
6. RSVP and see a ticket with QR code and ticket code.
7. Download Add to Calendar.
8. Switch to Alex Rivera.
9. Open My Events and then Check-in.
10. Enter Maya's ticket code manually.
11. See counters update.
12. Enter the same code again and see duplicate blocked.
13. Undo the last scan and see counters roll back.

After fixing issues, summarize the final route map, demo accounts, seeded scenarios, and any limitations. Do not claim repository README/report/sample CSV files were created.
```

## Compact Lovable Bug-Fix Prompt Template

Use this after browser testing finds a specific issue.

```text
Fix only the following issues in GatherPass. Do not redesign unrelated screens, replace the localStorage data model, introduce backend services, or change working flows.

Issue:
- Route:
- Demo account:
- Starting state:
- Steps to reproduce:
- Expected behavior:
- Actual behavior:
- Refresh persistence result:

Acceptance test:
- Starting from [route], signed in as [demo user], when I [action], the app should [result].
- Refresh the page and verify the state still persists.

Make the smallest reliable change and add clear success/error feedback where relevant.
```

## Manual Review Checklist

Use this quick checklist before deploying:

- Explore loads as the first useful screen.
- Upcoming filter is default; Include Past reveals past events.
- Public events show in Explore; Draft and Unlisted events do not.
- Unlisted events work by direct link.
- Event and Host pages update document title and meta description.
- Past event pages show Ended and hide RSVP.
- Signed-out RSVP redirects to Sign In and returns.
- RSVP produces either Going ticket or Waitlisted state.
- Canceling a confirmed RSVP promotes the first waitlisted attendee.
- Capacity increase promotes waitlisted attendees FIFO.
- Ticket has unique code, QR display, and calendar download.
- My Tickets shows confirmed and waitlisted upcoming events.
- Host can register, edit profile, create event, publish, unpublish, duplicate.
- Paid option is disabled with "Coming soon" tooltip.
- Dashboard stats update after RSVP, check-in, cancel, and undo.
- CSV export has exactly `name,email,RSVP status,check-in time`.
- Checker can manually check in, cannot duplicate, cannot check in invalid/waitlisted/cancelled codes, and can undo last scan.
- Gallery approval controls affect public gallery.
- Reports appear in review queue and hide/resolve works.
- My Events respects Host vs Checker quick actions.
- Demo seed includes one Host, one upcoming event, one past event, one draft event, and one unlisted event.

## Part 2: Stateful Lovable Cloud Migration Prompt Pack

The prompts below converted the working prototype into the official stateful submission.

The migration prompts below were used after the prototype was working.

Target app:
https://gather-pass-hub.lovable.app/

## Context

GatherPass first reached a working state as a browser-state prototype. The official submission is now the Lovable Cloud version. These prompts document the migration path: preserve the working UI and product behavior, then replace browser-local application data with shared backend persistence.

Key goals:

- Use Lovable Cloud only: database, auth, storage where useful, backend/RPC functions, logs, and security checks.
- Do not use a custom backend server, external Supabase project, payments, or a redesign.
- Preserve current routes, navigation, visual style, and review flows.
- Make users, hosts, events, RSVPs, tickets, check-ins, invites, feedback, gallery photos, and reports shared across users/sessions.
- Remove any public reset action because backend reset would affect all users.
- Use OpenAI Atlas browser as the independent UI test driver.

## Prompt 0: Migration Brief, No Implementation Yet

```text
GatherPass is already fully implemented as a Lovable app. This is not a new build. We are extending the existing solution by converting it from browser-local prototype persistence to a shared stateful Lovable Cloud backend.

Official target:
https://gather-pass-hub.lovable.app/

Goal:
Make users, hosts, events, RSVPs, tickets, check-ins, invites, feedback, gallery photos, and reports persist in Lovable Cloud so changes made by one user/browser/session are visible to other users/sessions.

Preserve the current app:
- Do not rebuild from scratch.
- Do not redesign the UI.
- Do not change the core route map.
- Do not remove working flows.
- Keep Explore, Event pages, Host pages, My Tickets, My Events, Host Dashboard, Event Editor, Check-in, feedback, gallery, reports, invites, CSV export, QR tickets, and Add to Calendar.
- Keep the practical event-operations feel.

Use Lovable Cloud only:
- Lovable Cloud database
- Lovable Cloud auth
- Lovable Cloud storage only where useful for uploaded images
- Lovable Cloud backend/RPC functions for race-prone mutations
- Lovable Cloud logs/security checks

Do not use:
- external Supabase project
- custom backend server
- payments
- route restructuring
- a new product direction

Important implementation facts:
- The previous app used browser-scoped state; the stateful version must replace it with Cloud data.
- It has seeded users: Maya, Jordan, Alex, Priya, Omar, Riley.
- It has seeded Host Brightside Collective.
- It has seeded events covering upcoming open, upcoming full, past, draft, and unlisted states.
- It has a public reset action that must be removed for the stateful backend version.

Before implementing, inspect the current app structure and reply with:
1. The current state/auth provider or equivalent state layer you found.
2. The exact Cloud tables you intend to create.
3. The backend functions or transaction-safe mutations you intend to create.
4. Which UI pieces should remain frontend-only.
5. The migration risks.
6. A short phase plan.

Do not implement yet.
```

## Prompt 1: Cloud Schema, Auth, And Seed Data

```text
Implement the Lovable Cloud foundation for the existing GatherPass app.

Official target:
https://gather-pass-hub.lovable.app/

This is an extension of the current working app, not a rebuild. Preserve the existing UI, routes, page structure, visual style, and feature behavior while adding Lovable Cloud persistence.

Create Cloud tables with appropriate IDs, timestamps, foreign keys, indexes, uniqueness constraints, and enum/check constraints:

- profiles: private user profile; id linked to auth user id; name; email; avatar; timestamps.
- public_profiles: public-safe mirror with id, name, avatar only.
- hosts: name, avatar, bio, contact_email, created_by, timestamps.
- host_members: host_id, user_id, role Host or Checker, timestamps, unique host_id + user_id.
- events: host_id, title, description, start_at, end_at, timezone, venue, online_link, capacity, cover_image_url, visibility Public or Unlisted, status Draft or Published, pricing Free, category, created_by, timestamps.
- rsvps: event_id, user_id, status Going/Waitlisted/Cancelled, created_at, cancelled_at, promoted_at, promotion_acknowledged.
- tickets: event_id, user_id, unique code, qr_payload, created_at, unique event_id + user_id.
- check_ins: event_id, ticket_code, user_id, checked_in_by, checked_in_at, unique ticket_code.
- invites: token, host_id, invite_type, role, created_at, expires_at, used_at, used_by_user_id.
- feedback: event_id, user_id, rating 1-5, comment, created_at, unique event_id + user_id.
- gallery_photos: event_id, user_id, image_url, caption, status Pending/Approved/Hidden, timestamps.
- reports: target_type Event or Photo, target_id, reporter_id, reason, status, timestamps.

Add SECURITY DEFINER helpers for RLS where needed, avoiding recursive policies.

Create seeded review accounts if Lovable Cloud auth supports it:
- maya@example.com / demo123
- jordan@example.com / demo123
- alex@example.com / demo123
- priya@example.com / demo123
- omar@example.com / demo123
- riley@example.com / demo123

If auth users cannot be seeded automatically, stop after creating the schema and tell me exactly which users to create manually in the Cloud Users UI before continuing.

Seed the canonical demo dataset:
- Host: Brightside Collective
- Jordan Lee is Host
- Alex Rivera is Checker
- One upcoming public event with capacity remaining
- One upcoming public full event with waitlist
- One past public event
- One draft event
- One unlisted published event
- Seeded Going, Waitlisted, Cancelled RSVP states
- Seeded ticket codes
- At least one checked-in ticket
- Feedback, gallery photos, and one open report

Do not redesign UI. After implementing, summarize created tables, seeded records, RLS intent, and any manual user setup required.
```

## Prompt 2: Replace State And Auth Wiring

```text
Replace the existing GatherPass browser-local app state with Lovable Cloud data while preserving existing app behavior.

Official target:
https://gather-pass-hub.lovable.app/

This is a state-layer migration. Do not rebuild pages from scratch. Keep the component-facing behavior of the current state/provider/hooks as stable as possible, but make shared application data come from Lovable Cloud.

Remove dependency on browser-scoped application state. Keep only harmless local UI preferences if any.

Auth:
- Replace prototype email/password checking with Lovable Cloud auth.
- Keep email/password sign-in and Create Account.
- Preserve redirect behavior after sign-in.
- Create or update the profiles row after signup/sign-in when needed.
- Signed-out users can browse Explore and public event/host pages.

Remove:
- Public reset button/action.
- Footer or UI copy claiming data persists only in the browser.

Public reads:
- Explore loads Published Public events from Cloud.
- Event detail loads Published events, including Unlisted events by direct URL.
- Draft events are visible only to Host members for that event's Host.
- Host pages load public Host profile and published events.

Shared state:
- Ensure changes from other sessions become visible after mutation, navigation, refresh, or realtime subscription.
- Prefer realtime subscriptions for core shared tables if Lovable Cloud supports them cleanly.

Acceptance tests:
- Sign in with seeded accounts.
- Sign out and browse Explore.
- Open public event details signed out.
- Refresh authenticated routes and confirm auth/session persistence.
- Confirm public reset is no longer available.

After implementing, provide a report-ready summary of the state/auth migration.
```

## Prompt 3: Backend RSVP, Tickets, And Waitlist

```text
Convert RSVP, ticketing, and waitlist behavior to safe backend-backed mutations.

Official target:
https://gather-pass-hub.lovable.app/

Keep the current UI and user flows. Move only the persistence and race-prone state transitions to Lovable Cloud/backend logic.

Implement backend RPCs or transaction-safe database mutations for:
- rsvp_to_event(event_id)
- cancel_rsvp(event_id)
- promote_waitlist(event_id)
- update_event_capacity(event_id, new_capacity)

Rules:
- RSVP requires authenticated user.
- Upcoming Published events only.
- If Going count is below capacity, create Going RSVP and a unique ticket.
- If capacity is full, create Waitlisted RSVP and no confirmed ticket.
- Prevent duplicate active RSVP by the same user for the same event.
- Canceling a Going RSVP sets status to Cancelled and promotes the oldest Waitlisted attendee FIFO.
- Increasing capacity promotes waitlisted attendees FIFO until capacity is filled.
- Promotion sets promoted_at and creates a ticket if needed.
- Ticket codes must be globally unique and stable.
- Waitlisted and Cancelled users cannot access confirmed ticket pages.

Keep:
- Existing ticket page design.
- Existing QR display.
- Existing Add to Calendar behavior.
- Existing My Tickets page split between Going tickets and Waitlisted events.

Acceptance tests:
- RSVP under capacity creates Going status and ticket.
- RSVP at capacity creates Waitlisted status.
- Cancel Going RSVP and confirm the first waitlisted attendee is promoted.
- Increase capacity as Host and confirm FIFO promotion.
- Confirm owner-only ticket access still holds.

After implementing, provide a report-ready summary of backend RSVP/ticket/waitlist decisions and tests.
```

## Prompt 4: Backend Host, Roles, Check-In, And Moderation

```text
Convert Host operations, roles, check-in, feedback, gallery, reports, and invites to Lovable Cloud persistence.

Official target:
https://gather-pass-hub.lovable.app/

Do not rebuild the pages. Preserve current navigation, role-specific visible actions, route guards, feedback, and status messaging. Move shared state and permission-sensitive mutations to Cloud.

Host operations:
- Host registration creates hosts and host_members rows.
- Event editor creates/updates events in Cloud.
- Publish, Unpublish, Duplicate, and capacity increase work with backend state.
- CSV export reads Cloud RSVPs/check-ins and keeps exact headers:
  name,email,RSVP status,check-in time

Roles:
- Host role can manage events, dashboard, exports, invites, gallery approval, and reports.
- Checker role can access check-in only.
- Attendees and signed-out users cannot access protected Host/Checker actions.
- My Events aggregates events for Host/Checker memberships from Cloud.

Invites:
- Host can create Host or Checker invite links.
- Invite tokens are single-use and expiring.
- Signed-out invite visitors are sent to sign-in and returned to accept the invite.
- Prevent duplicate membership rows.

Check-in:
- Implement check_in_ticket(event_id, ticket_code) as a backend function.
- Implement undo_check_in(check_in_id) as a backend function.
- Valid Going ticket for the event succeeds.
- Duplicate check-in is blocked.
- Invalid, Waitlisted, Cancelled, and wrong-event tickets are rejected.
- Counters update from Cloud state.

Feedback/gallery/reports:
- Feedback allowed only after event end and from authenticated attendees.
- Gallery uploads create Pending rows.
- Approved photos are public; Pending/Hidden are not public.
- Hosts can approve/hide photos.
- Reports create Cloud rows and appear in Host review queue.
- Hosts can resolve/hide reported items.

Acceptance tests:
- Host creates/publishes event; another signed-out session sees it in Explore.
- Checker sees check-in only, not Host management.
- Manual check-in updates counters and persists after refresh.
- Duplicate/invalid/waitlisted/cancelled codes are rejected.
- Invite acceptance works after sign-in and cannot be reused.
- Gallery/report moderation persists across sessions.

After implementing, provide a report-ready summary of role, check-in, and moderation migration.
```

## Prompt 5: RLS, Security Scan, And Final Hardening

```text
Harden the Lovable Cloud backend with Row Level Security and run Lovable security checks.

Official target:
https://gather-pass-hub.lovable.app/

RLS policy intent:
- Public/anon can read published public Host/Event information needed for browsing.
- Public/anon can read Published Unlisted event details by direct link, but Unlisted events are not listed in Explore.
- Draft events are readable only by Host members for the event's Host.
- Authenticated users can read/update their own profile.
- Public profile display uses public_profiles only, with no email exposure.
- Attendees can read only their own RSVPs and ticket details.
- Ticket pages are owner-only and must not leak another user's ticket details.
- Hosts can manage rows for Hosts where they have Host role.
- Checkers can read only the event/check-in data needed for assigned Host check-in.
- Feedback writes require authenticated eligible users; reads are limited to author or relevant Host.
- Gallery Approved photos are public; Pending/Hidden are restricted to uploader or Host.
- Reports are restricted to relevant Hosts.
- Invite acceptance must not expose unnecessary token details.

Security requirements:
- No service-role key in frontend code.
- No client-side bypass for Host/Checker permissions.
- Race-prone actions remain backend/transaction-safe.
- Expired or used invite tokens cannot be accepted.
- Direct route tests should match visible UI permissions.

Run Lovable's security scan after applying policies. Fix all critical/high findings and any medium finding related to auth, RLS, ticket privacy, invites, feedback privacy, or Host/Checker permissions.

Acceptance tests:
- Signed-out public browsing works.
- Attendee cannot access Host Dashboard, check-in, other users' tickets, draft events, or moderation queues.
- Checker cannot edit/export/manage Host dashboard.
- Host can manage only their Host.
- Used/expired invite links fail safely.
- Two-session shared-state tests still pass after RLS.

After implementing, provide a report-ready security and hardening summary.
```

## Prompt 6: Atlas Final QA Pass

```text
Run a final requirement-by-requirement QA pass on GatherPass.

Target app:
https://gather-pass-hub.lovable.app/

Use OpenAI Atlas browser as the independent UI test driver. Test as a real reviewer first:
- Prefer visible navigation and user-discoverable flows before direct URL checks.
- If a feature works only by typing a known URL but has no visible entry point for the relevant role, mark it as FAIL.
- Use at least two sessions, windows, or browser contexts where possible to prove backend state is shared across users.

Test scenarios:
1. Signed-out user browses Explore and event detail pages.
2. Seeded attendee signs in and RSVPs.
3. Host sees RSVP/dashboard counts update from shared backend data.
4. Attendee views owner-only ticket.
5. Checker checks in ticket manually.
6. Host and attendee sessions reflect check-in state.
7. Duplicate check-in is blocked.
8. Undo last check-in persists and updates counters.
9. Host creates/publishes an event and another session sees it.
10. Draft and Unlisted behavior remains correct.
11. FIFO waitlist promotion works after cancellation and capacity increase.
12. CSV export still uses exact required headers.
13. Feedback, gallery approval, reports, and invite acceptance persist across sessions.
14. Public reset action is absent.

Security and regression checks:
- Attendee cannot access Host Dashboard, check-in page, other users' tickets, draft events, or moderation queue.
- Checker cannot edit events, export CSV, or manage Host dashboard.
- Host cannot manage unrelated Host data if multiple Hosts exist.
- Used or expired invite links fail safely.
- No primary route still depends on browser-local app state.
- No UI copy says data is browser-local.
- No placeholder pages.

Return:
- PASS/FAIL by feature area.
- Atlas session setup used.
- Evidence of shared backend state.
- Any blocking issues.
- Any known limitations.
- A concise report-ready paragraph explaining why the app is stateful.
```

## Atlas Bug-Fix Prompt Template

```text
Fix only this confirmed issue in the stateful GatherPass app. Do not redesign unrelated screens, change routes, or refactor broad areas. Preserve the existing Lovable Cloud architecture and working flows.

Target app:
https://gather-pass-hub.lovable.app/

Failed Atlas UI test:
- Checkpoint:
- Route tested:
- Account used:
- Starting state:
- Steps to reproduce:
- Expected behavior:
- Actual behavior:
- Refresh/cross-user persistence result:
- Console/backend error if visible:

Scope:
- Fix the smallest reliable cause.
- Do not reintroduce browser-local app-data writes.
- Do not touch unrelated write flows.
- Keep existing UI text and layout unless the failure is UI-specific.

Acceptance test:
- Starting from [route], signed in as [user], when I [action], the app should [result].
- Refresh the page and verify the result persists where relevant.
- If another role/user should observe the result, sign in as that user and verify it.

Report back with:
1. Root cause.
2. Files/RPCs/policies changed.
3. Manual test result.
4. Any remaining blocker.
```

## Report Notes Extracted From The Migration

- The official app is stateful and deployed at https://gather-pass-hub.lovable.app/.
- The browser-state prototype was useful for quickly proving the flow, but backend persistence was required for multi-user/session behavior.
- Shared entities moved into Lovable Cloud tables, and prototype auth was replaced with Cloud auth plus profiles.
- Race-prone flows such as RSVP capacity enforcement, FIFO waitlist promotion, check-in, undo check-in, and invite acceptance moved to backend mutations.
- Public reset was removed because backend reset would affect every user/session.
- OpenAI Atlas browser was used as the independent UI driver for shared-state validation and visible-navigation-first QA.
