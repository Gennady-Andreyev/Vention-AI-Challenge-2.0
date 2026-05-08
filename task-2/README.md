# GatherPass

GatherPass is a stateful Lovable Cloud application for hosting free community events, collecting RSVPs, issuing QR tickets, and checking attendees in at the venue.

Official deployment URL: https://gather-pass-hub.lovable.app/

## Submission Artifacts

| Required artifact from `task.md` | Status | Location / notes |
|----------------------------------|--------|------------------|
| Shareable public URL to a working deployed application | Done | https://gather-pass-hub.lovable.app/ |
| Deployed app seeded with at least one Host, one upcoming event, and one past event | Done | Brightside Collective; Sunset Sketch Walk; Spring Picnic Potluck |
| Example CSV export file with the correct schema | Done | [example-rsvp-export.csv](example-rsvp-export.csv) |
| Technical report covering tools, techniques, what worked, what did not, and notable decisions | Done | [report.md](report.md) |
| Step-by-step README usage guide for Publish -> RSVP -> Ticket -> Check-in | Done | This file |
| Public GitHub repository with the project in `task-2/` | Done | https://github.com/Gennady-Andreyev/Vention-AI-Challenge-2.0/tree/main/task-2 |

## Documentation Map

- [Usage guide](README.md)
- [Challenge brief](task.md)
- [Technical report](report.md)
- [Final test report](final-test-report.md)
- [Lovable prompt pack](lovable-prompts.md)
- [Claude and Atlas UI test scenarios](testing-approach.md)

## Implementation Note

GatherPass began as a deterministic browser-state prototype and was then migrated in a Lovable remix to the current stateful Lovable Cloud version. The Cloud version is now the official submission. It uses shared backend persistence, Cloud auth, row-level security, backend RPCs for race-sensitive actions, and no public reset action.

## Seeded Accounts

The app uses Lovable Cloud auth. The seeded review accounts use email/password sign-in:

| Account | Email | Password | Role | Use for |
|---------|-------|----------|------|---------|
| Maya Chen | maya@example.com | demo123 | Attendee | RSVP, tickets, feedback, gallery upload |
| Jordan Lee | jordan@example.com | demo123 | Host | Event publishing, dashboard, exports, moderation |
| Alex Rivera | alex@example.com | demo123 | Checker | My Events and event check-in |
| Priya Shah | priya@example.com | demo123 | Attendee | Waitlist and promotion checks |
| Omar Hassan | omar@example.com | demo123 | Attendee | RSVP and waitlist checks |
| Riley Morgan | riley@example.com | demo123 | Attendee | Invite and edge-case checks |

## Seeded Cloud Data

The deployed Cloud backend includes a seeded review dataset:

- Host: Brightside Collective.
- Upcoming open event: Sunset Sketch Walk.
- Upcoming full event: Community Coding Night.
- Past event: Spring Picnic Potluck.
- Draft event: Autumn Lantern Festival (Draft).
- Unlisted event: Members-Only Studio Tour.
- Seeded RSVPs, waitlist entries, tickets, check-ins, feedback, gallery photos, and one open report.

Because the app now uses shared backend state, there is no public reset action.

## Main Flow: Publish -> RSVP -> Ticket -> Check-in

### 1. Publish an Event

1. Sign in as Jordan Lee with `jordan@example.com` / `demo123`.
2. Open Host Dashboard from the navigation.
3. Choose New Event, or edit an existing event.
4. Fill in the event title, description, start and end date/time, timezone, venue or online link, capacity, cover image, visibility, and status.
5. Leave pricing set to Free. Paid is intentionally disabled with a "Coming soon" tooltip.
6. Save as Draft if the event is not ready, or Publish when it should be public.
7. Confirm that Public published events appear in Explore. Unlisted published events stay hidden from Explore but work by direct link.

Useful host actions:

- Publish and Unpublish control public availability.
- Duplicate creates a draft copy.
- Increasing capacity promotes waitlisted attendees FIFO.
- Export CSV downloads RSVP and attendance data.

### 2. RSVP as an Attendee

1. Sign out.
2. Open Explore.
3. Open Sunset Sketch Walk or another upcoming published event.
4. Click RSVP while signed out.
5. Sign in as an attendee, for example `maya@example.com` / `demo123`.
6. Confirm the app returns to the same event page.
7. Click RSVP.

If capacity is available, the attendee becomes Going and receives a ticket immediately. If an event is full, the RSVP moves to the waitlist instead.

### 3. View the Ticket

1. After RSVP, open the ticket from the event page or My Tickets.
2. Confirm the ticket shows a unique code and QR code.
3. Use Add to Calendar to download an `.ics` file.
4. Open My Tickets to see upcoming Going tickets and Waitlisted events.

Past events show Ended and hide RSVP. Past event pages expose feedback and gallery actions instead.

### 4. Check In at the Venue

1. Sign out, then sign in as Alex Rivera with `alex@example.com` / `demo123`.
2. Open My Events.
3. Choose Check-in for the relevant event.
4. Enter a Going attendee's ticket code manually.
5. Confirm the app shows a successful check-in and updates the Going, Checked-in, Remaining, and Waitlist counters.
6. Enter the same code again to confirm duplicate check-ins are blocked.
7. Use Undo last scan to roll back the most recent successful check-in.

Camera scanning is not required for this submission; QR tickets are generated, and manual code entry is sufficient.

## Other Review Flows

- Explore supports text search, date range, location filter, Upcoming default, and Include Past.
- Host Dashboard shows Upcoming and Past events with Going, Waitlist, and Checked-in counts.
- My Events aggregates events for users with Host or Checker roles and shows role-appropriate actions.
- Ticket pages are owner-only; Hosts and Checkers validate ticket codes through the check-in page.
- Host invite links can grant Host or Checker access and are single-use.
- Attendees can submit post-event feedback with a 1-5 rating and optional comment.
- Gallery uploads start Pending and require Host approval before public display.
- Event and photo reports appear in the Host review queue and can be resolved or hidden.

## CSV Export

The required example CSV artifact is included in this folder as `example-rsvp-export.csv`.

The in-app export uses these exact columns:

```csv
name,email,RSVP status,check-in time
```

When `check-in time` is populated, it should be exported as a timezone-aware UTC timestamp in ISO 8601 format, for example `2026-05-12T18:08:00.000Z`. Rows for attendees who have not checked in should leave the field blank.
