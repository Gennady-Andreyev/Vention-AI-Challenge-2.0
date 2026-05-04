# GatherPass UI Test Scenario for Claude and OpenAI Atlas

This file records the browser QA scenario used with Claude and the updated all-round browser test to run in OpenAI Atlas.

- Claude browser extension was used earlier as the independent UI test driver for the first full QA pass.
- OpenAI Atlas is used alongside Claude for the updated all-round pass, especially after the authentication UI correction.
- The prompt below is written for Atlas, but the scenario matrix is also suitable for any browser-based QA agent.

```text
You are the independent UI test driver for the GatherPass app.

App URL:
https://gather-event-joy.lovable.app

Goal:
Run an all-round browser-only QA pass against the Task 2 requirements. Use only the visible UI. Do not inspect source code. Do not rely on prior Lovable, Codex, Claude, or self-QA reports. Treat this as a fresh organizer/reviewer acceptance test.

Important latest requirement focus:
The app must not rely only on visible mock-user shortcuts. It should provide normal local demo authentication:
- Sign In form with email + password.
- Create Account form.
- Seeded users should sign in like normal users.
- Demo/reviewer one-click account cards should not be shown unless they are hidden behind non-primary tooling. The main auth UI should not look like a mock.

Seeded user credentials expected after Reset demo data:
- Maya Chen: maya@example.com / demo123
- Jordan Lee: jordan@example.com / demo123
- Alex Rivera: alex@example.com / demo123
- Priya Shah: priya@example.com / demo123
- Omar Brooks: omar@example.com / demo123
- Riley Morgan: riley@example.com / demo123

Known seeded entities:
- Host: Brightside Collective.
- Upcoming open event: /events/e_upcoming_open
- Upcoming full event: /events/e_upcoming_full
- Past event.
- Draft event: /events/e_draft
- Unlisted event: /events/e_unlisted
- Host page: /hosts/h_brightside
- Host Dashboard: /host
- New Event Editor: /host/events/new
- My Events: /my-events

Testing rules:
- Start with Reset demo data.
- Use the browser UI only.
- Refresh after important state changes to verify localStorage persistence.
- Mark placeholder pages, inert buttons, missing feedback, or silent failures as defects.
- Treat `task.md` as the source of truth. If this prompt and the app disagree with `task.md`, report the app behavior as a risk or bug.
- Test feature discoverability before testing known routes. For Host registration, Host Dashboard, Event Editor, My Events, Tickets, Check-in, and moderation queues, first try to reach the feature through visible navigation, account menus, contextual CTAs, or page links. Direct URL navigation is allowed only after you verify there is a real UI path, or when a scenario explicitly tests route guards.
- If a feature works by typing a known URL but has no visible UI entry point for the relevant user role, mark it as FAIL. This is a user-experience availability bug, not a pass.
- Use unique emails for created accounts, for example atlas.tester+[timestamp]@example.com.
- If a file download cannot be inspected because of browser restrictions, report the download behavior separately from content inspection.
- Output concise evidence, not a long narrative.

Output format:
1. Overall result: PASS / PARTIAL PASS / FAIL.
2. A scenario table with columns: Scenario, Result, Evidence, Notes.
3. A "Blocking bugs" section.
4. A "Navigation/discoverability gaps" section.
5. A "Non-blocking risks" section.
6. For each failed or partial scenario, provide a copy-paste Lovable fix prompt with route, account, steps, expected behavior, actual behavior, persistence result, and minimal requested fix.

Scenario 1: Initial app and reset
Steps:
- Open the app URL.
- Use Reset demo data.
- Confirm `/` lands on or redirects to Explore.
- Refresh.
Pass criteria:
- Explore is the first useful screen.
- Reset restores the seeded app state.
- Refresh does not break the session or seed.

Scenario 2: Auth UI is real sign-in/sign-up, not mock shortcuts
Steps:
- Open `/signin`.
- Inspect the page before signing in.
Pass criteria:
- A normal Sign In form is visible with email and password fields.
- A Create Account mode/form is available.
- There is no large visible "Demo accounts" section with no-password one-click user cards.
- If demo helpers exist, they are not the primary auth experience and do not make the page look like a mock.

Scenario 3: Create Account validation
Steps:
- Open `/signin`.
- Switch to Create Account.
- Try empty fields.
- Try invalid email.
- Try password shorter than 6 characters.
- Try mismatched password confirmation.
Pass criteria:
- Each invalid state shows visible error feedback.
- The form does not silently fail.
- No invalid user is created.

Scenario 4: Create Account success and persistence
Steps:
- Create a user:
  - Full name: Atlas Tester
  - Email: atlas.tester+[timestamp]@example.com
  - Password: testpass123
- Confirm the user is signed in.
- Refresh.
- Sign out.
- Sign in again with the same email/password.
- Try creating another account with the same email.
Pass criteria:
- New user is created in local demo state.
- New user is signed in immediately after creation.
- Session and user persist after refresh.
- Email/password sign-in works after sign-out.
- Duplicate email is rejected with visible feedback.

Scenario 5: Sign In validation and seeded credentials
Steps:
- Sign out.
- Try unknown email.
- Try known email with wrong password.
- Sign in as Maya with maya@example.com / demo123.
- Sign out.
- Sign in as Jordan with jordan@example.com / demo123.
- Sign out.
- Sign in as Alex with alex@example.com / demo123.
Pass criteria:
- Unknown email and wrong password show visible errors.
- Seeded users authenticate through email/password.
- Sign-out works.
- No one-click account switching is required.

Scenario 6: Public browsing and Explore filters
Steps:
- Sign out.
- Open Explore.
- Confirm Upcoming is default.
- Use text search.
- Use location filter.
- Use date range filter.
- Enable Include Past.
- Open a past event.
Pass criteria:
- Signed-out users can browse public published events.
- Filters change results appropriately.
- Past events appear when Include Past is enabled.
- Past event pages show Ended and hide RSVP.

Scenario 7: Public, draft, and unlisted visibility
Steps:
- Sign out.
- Confirm public events appear in Explore.
- Confirm `/events/e_unlisted` works by direct link.
- Confirm `/events/e_draft` does not expose event details or RSVP.
- Sign in as Maya and open `/events/e_draft`.
- Sign in as Alex and open `/events/e_draft`.
- Sign in as Jordan and open `/events/e_draft`.
Pass criteria:
- Draft events are hidden from signed-out users, attendees, and checkers.
- Only owning Host can preview/manage draft.
- Unlisted event is hidden from Explore but reachable by direct link.

Scenario 8: Signed-out RSVP redirect with sign-in
Steps:
- Reset demo data.
- Sign out.
- Open `/events/e_upcoming_open`.
- Click RSVP.
- Confirm redirect to `/signin?redirect=/events/e_upcoming_open`.
- Sign in as Maya with email/password.
Pass criteria:
- User returns to the original event page after sign-in.
- RSVP can be completed without manually finding the event again.

Scenario 9: Signed-out RSVP redirect with account creation
Steps:
- Reset demo data.
- Sign out.
- Open `/events/e_upcoming_open`.
- Click RSVP.
- Create a new account from the redirected sign-in page.
- Return to the event and RSVP.
- Open My Tickets.
Pass criteria:
- Create Account preserves redirect.
- New user can RSVP.
- New user gets a ticket and can see it in My Tickets.

Scenario 10: RSVP under capacity, ticket, QR, and calendar
Steps:
- Reset demo data.
- Sign in as Maya.
- Open `/events/e_upcoming_open`.
- RSVP.
- Open the ticket.
- Click Add to Calendar.
- Refresh and open My Tickets.
Pass criteria:
- RSVP status becomes Going.
- Unique ticket code and QR are shown.
- Ticket code is unique compared with other visible seeded or newly created ticket codes.
- `.ics` download is triggered.
- Ticket persists after refresh.
- My Tickets shows all upcoming Going tickets for the signed-in user, not only the newest one.

Scenario 10A: Ticket ownership and direct ticket URL access
Steps:
- Reset demo data.
- Sign in as Maya.
- RSVP to `/events/e_upcoming_open` if needed.
- Open Maya's ticket and copy the ticket URL or ticket code.
- Sign out.
- Open Maya's ticket URL while signed out.
- Sign in as Priya and open Maya's ticket URL.
- Sign in as Omar and open Maya's ticket URL.
- Sign in as Alex and open Maya's ticket URL.
- Sign in as Jordan and open Maya's ticket URL.
- Sign back in as Maya and open Maya's ticket URL.
Pass criteria:
- Signed-out ticket URL access redirects to sign-in with redirect preserved.
- Only Maya can view Maya's ticket.
- Other signed-in users see a neutral denied/not-found state.
- The denied state does not leak attendee name, email, QR code, event-specific ticket details, or whether the ticket code exists.
- Hosts and Checkers validate codes through the check-in page, not through owner ticket pages.

Scenario 11: Full event waitlist
Steps:
- Reset demo data.
- Sign in as Priya or a new attendee not already Going.
- Open `/events/e_upcoming_full`.
- RSVP if not already waitlisted.
- Open My Tickets.
Pass criteria:
- Full event does not exceed capacity.
- User is Waitlisted, not ticketed as Going.
- Waitlist state is visible in My Tickets.

Scenario 12: FIFO promotion after cancellation
Steps:
- Reset demo data.
- Use the full event with Omar Going and Priya/Riley waitlisted.
- Sign in as Omar and cancel the Going RSVP.
- Sign in as Priya.
- Check the event and My Tickets.
- Sign in as Riley.
- Check the event and My Tickets.
Pass criteria:
- A Going attendee can cancel their RSVP from the event or ticket flow.
- Priya is promoted before Riley.
- Priya has Going status and ticket/promotion notice.
- Riley remains Waitlisted.
- Counts stay valid.

Scenario 12A: Runtime waitlist promotion after cancellation and login notification
Steps:
- Reset demo data.
- Sign in as Jordan and create or edit a future Public Published event with capacity `1`. Use visible UI only.
- Sign out.
- Sign in as user A, preferably Maya, and RSVP to the event. Confirm user A is Going and has a ticket.
- Sign out.
- Sign in as user B, preferably Priya, and RSVP to the same event. Confirm user B is Waitlisted and does not have a confirmed ticket.
- Sign out user B before the cancellation happens.
- Sign in as user A and cancel the RSVP from the event page, ticket page, or My Tickets.
- Sign out user A.
- Sign in again as user B.
- Check the first screen after login, My Tickets, and the event detail page.
Pass criteria:
- The event never exceeds capacity.
- User B is automatically promoted from Waitlisted to Going after user A cancels.
- User B receives a ticket after promotion.
- User B sees an in-app promotion notification/banner/message on login or in My Tickets. It must be visible without typing a direct route or inspecting localStorage.
- User B is no longer shown as Waitlisted for that event.
- User A's cancelled RSVP no longer counts as Going.
- The promotion is persisted after refresh.

Scenario 13: FIFO promotion after capacity increase
Steps:
- Reset demo data.
- Sign in as Jordan.
- Edit/manage `/events/e_upcoming_full`.
- Increase capacity by 1 and save.
- Sign in as Priya and check status.
- Sign in as Riley and check status.
Pass criteria:
- Priya is promoted before Riley.
- Priya has ticket or promotion notice.
- Riley remains Waitlisted.
- Dashboard/event counts update and persist after refresh.

Scenario 14: Host registration as a new user
Steps:
- Sign in as the Atlas-created user or create a fresh user.
- Starting from the normal signed-in UI, find the visible path to Host registration. Check the top navigation, profile/account menu, empty states, and relevant page CTAs. Do not type a known Host registration URL unless you first find a visible entry point.
- Open Host registration through that visible UI path.
- Create a Host profile with name, logo/avatar, short bio, and contact email.
- Open the new public Host page.
- From the visible Host UI, find the New Event/Create Event action. Do not type the event editor URL unless the UI path exists.
- Create a new event.
- Save as Draft.
- Publish it.
- From visible navigation, open Host Dashboard for the new Host.
Pass criteria:
- A signed-in non-host user has a visible, understandable way to start Host registration.
- Any signed-in user can register as Host.
- New Host profile persists with name, logo/avatar, short bio, and contact email.
- Public Host page displays the Host profile and published events.
- A newly registered Host has visible navigation to create events and reach the Host Dashboard.
- New Host can create and publish a Public or Unlisted free event.
- New event can be managed from Host Dashboard.

Scenario 15: Event editor validation and lifecycle
Steps:
- Sign in as Jordan.
- Starting from the normal signed-in UI, reach Host Dashboard through visible navigation or account/menu affordances. Do not type `/host` as the first step.
- From Host Dashboard, use the visible New Event/Create Event action to open the event editor. Do not type `/host/events/new` unless you have already verified the visible action exists.
- Confirm the editor exposes fields for title, description, start date/time, end date/time, timezone, venue address or online link, capacity, cover image, Public/Unlisted visibility, Draft/Published state, and Free/Paid.
- Try saving/publishing with empty required fields.
- Try end date/time before start date/time.
- Create a valid draft with all required event fields completed.
- Publish, Unpublish, and Duplicate it.
- Check Free/Paid toggle.
Pass criteria:
- Jordan has a visible UI path to Host Dashboard and New Event.
- The editor includes every field required by `task.md`.
- Visible validation appears for empty and invalid date fields.
- Draft, Publish, Unpublish, and Duplicate work.
- Duplicate creates a Draft copy.
- Public published events are searchable in Explore.
- Unlisted published events are hidden from Explore but reachable by direct link.
- Paid is visible but disabled with "Coming soon" explanation.

Scenario 16: Host Dashboard and CSV export
Steps:
- Sign in as Jordan.
- Starting from Explore or another normal signed-in page, find and use the visible UI path to Host Dashboard. Do not type `/host` unless you have already verified the visible entry point exists.
- Inspect Upcoming and Past event sections.
- Export CSV for an event.
Pass criteria:
- A Host user can discover and open Host Dashboard from the visible UI.
- Event cards/rows show Going, Waitlist, Checked-in counts.
- CSV download is triggered.
- If content can be inspected, headers are exactly: name, email, RSVP status, check-in time.
- If content can be inspected, rows include attendee name, email, RSVP status, and blank or populated check-in time in a spreadsheet-safe comma-separated format.
- Populated check-in times are timezone-aware UTC ISO timestamps ending in `Z`, for example `2026-05-12T18:08:00.000Z`.
- Seeded initial check-ins export non-empty UTC check-in times.

Scenario 16A: Runtime check-in CSV timestamp and undo consistency
Steps:
- Reset demo data.
- Sign in as Maya.
- RSVP to `/events/e_upcoming_open` if needed and copy Maya's ticket code.
- Sign in as Alex or Jordan.
- Open the check-in page through visible UI.
- Enter Maya's ticket code and confirm successful check-in.
- Sign in as Jordan if not already Host.
- Export CSV for the checked-in event.
- Inspect the downloaded CSV if the browser allows it.
- Return to the check-in page and use Undo last scan.
- Export CSV for the same event again.
Pass criteria:
- Runtime check-in creates a persisted check-in timestamp.
- Maya's exported `check-in time` is non-empty after check-in.
- The timestamp is timezone-aware UTC ISO ending in `Z`.
- Undo last scan clears Maya's exported `check-in time`.
- Counters and CSV stay consistent after refresh.

Scenario 17: Roles and route guards
Steps:
- Sign out and try `/host`, `/my-events`, and check-in route.
- Sign in as Maya and try the same protected routes.
- Sign in as Alex and find My Events/check-in through visible navigation before trying direct routes.
- Sign in as Jordan and find Host Dashboard through visible navigation before trying direct routes.
Pass criteria:
- Signed-out users are redirected to sign-in.
- Attendee cannot access Host/Checker protected actions.
- Attendee UI should still provide a visible Host registration path, because any signed-in user can register as a Host.
- Checker can discover My Events/check-in from visible UI.
- Checker can access check-in only.
- Checker cannot edit events, export CSV, or manage Host Dashboard.
- Host can discover Host Dashboard from visible UI.
- Host can access management actions.

Scenario 18: Invite links after auth
Steps:
- Reset demo data.
- Sign in as Jordan.
- Reach Host member/invite management through visible Host UI navigation.
- Generate/copy a Checker invite link.
- Generate/copy a Host invite link.
- Confirm each generated invite shows an expiry or otherwise communicates that the link is time-limited.
- Sign out.
- Open the Checker invite link.
- Sign in or create an account.
- Open My Events.
- Accept the same Checker invite twice if possible.
- Try reusing the same Checker invite link as another non-member user.
- Repeat the flow with the Host invite link using a different non-member user.
Pass criteria:
- Host member/invite management is discoverable from Host UI.
- Invite survives auth redirect.
- Both Host and Checker invite links are copyable.
- Invite links are time-limited and single-use.
- Checker invite grants Checker role.
- Checker access is check-in only.
- Host invite grants Host management access.
- Reusing an already-used invite does not grant membership and shows a clear safe error.
- Duplicate memberships are not created.

Scenario 19: My Events
Steps:
- Sign in as Alex.
- Open My Events through visible navigation. Do not type `/my-events` unless the UI path has already been verified.
- Use Host filter.
- Use date range filter.
- Use text search.
- Inspect actions.
- Repeat as Jordan.
Pass criteria:
- My Events is visible to Host/Checker users.
- My Events is discoverable from visible navigation for users with roles.
- Filters work.
- Checker sees check-in actions only.
- Host sees edit/dashboard/export/check-in actions.

Scenario 20: Check-in happy path
Steps:
- Reset demo data.
- Sign in as Maya.
- RSVP to `/events/e_upcoming_open` if needed and copy the ticket code.
- Sign in as Alex.
- Open check-in for that event.
- Enter Maya's ticket code.
- Refresh.
Pass criteria:
- Valid Going ticket checks in successfully.
- Counters update.
- Recent scans show the successful scan.
- Check-in persists after refresh.

Scenario 21: Check-in error cases and undo
Steps:
- Sign in as Alex.
- Enter the same code again.
- Enter an invalid code.
- Enter a waitlisted ticket code if visible.
- Enter a cancelled ticket code if visible.
- Undo the last successful scan.
Pass criteria:
- Duplicate check-in is blocked.
- Invalid code is rejected.
- Waitlisted and Cancelled tickets are rejected.
- Undo removes only the last successful check-in and updates counters.

Scenario 22: Post-event feedback
Steps:
- Sign in as Maya.
- Open a past event.
- Try submitting feedback without rating.
- Submit 1-5 star rating with optional comment.
- Refresh.
- Open an upcoming event.
Pass criteria:
- Feedback appears only for past events.
- Rating is required.
- Comment is optional.
- Feedback persists.
- Upcoming event does not show feedback form.

Scenario 23: Gallery upload and approval
Steps:
- Reset demo data.
- Sign in as Maya.
- Open a past event.
- Upload or add a photo.
- Confirm it is Pending and not public.
- Open an upcoming event and confirm gallery upload is not available before the event ends.
- Sign in as Jordan Lee (`jordan@example.com` / `demo123`), Host of Brightside Collective.
- Open Host Dashboard (`/host`) or reach it through visible Host navigation.
- Scroll down far enough to inspect the actual Gallery approval queue item cards, not only the "Gallery approval queue" heading.
- Locate rendered pending gallery cards and their actions, including Approve and Hide.
- Compare any pending/gallery queue count shown in the UI with the number of rendered queue cards.
- Approve the photo.
- Return to the public event page.
- Hide a photo.
Pass criteria:
- Attendee gallery upload is available after the event ends.
- Gallery upload is not available for upcoming events.
- Pending uploads are not public.
- With seeded demo data, Gallery approval queue renders pending item cards for Brightside Collective.
- Pending/gallery queue counts are consistent with the number of rendered queue cards after scrolling through the queue area.
- Host can approve photos.
- Approved photos become public.
- Hidden photos disappear publicly.

Scenario 24: Reports and review queue
Steps:
- Reset demo data.
- Sign out.
- Report a public event with a reason.
- If a public approved photo is visible while signed out, report that photo with a reason.
- Sign in as Maya or Priya.
- Report another event with a reason.
- Report a visible photo with a reason.
- Sign in as Jordan Lee (`jordan@example.com` / `demo123`), Host of Brightside Collective.
- Open Host Dashboard (`/host`) or reach it through visible Host navigation.
- Scroll down far enough to inspect the actual Report review queue item cards, not only the "Report review queue" heading.
- Locate rendered open report cards and their actions, including Resolve and Hide item.
- Compare any open/report queue count shown in the UI with the number of rendered queue cards.
- Resolve one report.
- Hide one reported item.
Pass criteria:
- Reporting is available to any user, including signed-out users, unless the app provides a clearly justified sign-in gate that should be flagged as a task.md risk.
- Users can report both events and photos.
- With seeded demo data, Report review queue renders open report cards for Brightside Collective.
- Open/report queue counts are consistent with the number of rendered queue cards after scrolling through the queue area.
- Resolve does not hide content.
- Hide removes reported item from public display.
- Management views show clear statuses.

Scenario 25: Metadata, persistence, and responsive pass
Steps:
- Navigate through Explore -> event detail -> Host page -> My Tickets -> Host Dashboard -> Check-in.
- Check browser title changes for Event and Host pages.
- Inspect or infer `meta[name="description"]` for Event and Host pages if Atlas can access page metadata.
- Resize to mobile width and repeat key flows: sign-in, RSVP, ticket, check-in.
- Refresh after several state changes.
Pass criteria:
- Event and Host pages use specific page titles and metadata if inspectable.
- If metadata is not inspectable in Atlas, mark only metadata inspection as inconclusive and continue testing visible behavior.
- Mobile layout remains usable.
- Text does not overlap or spill.
- Important actions show success/error feedback.
- Refresh preserves relevant local state.

Scenario 26: Submission artifact and seed checklist
Steps:
- Confirm the deployed app URL is reachable.
- Confirm Reset demo data includes at least one Host, one upcoming event, and one past event.
- Confirm the repository/package being reviewed includes `task-2/README.md`, `task-2/report.md`, and an example CSV export artifact if Atlas has repo access.
- If Atlas does not have repo access, mark repository artifact inspection as not testable from browser UI.
Pass criteria:
- Public deployed URL works.
- Seed contains at least one Host, one upcoming event, and one past event.
- Repository artifacts are present if inspectable: usage guide README, report.md, and example CSV with required schema.
- Missing repository artifact access should be reported as "not inspectable", not as an app failure.

Scenario 27: Reset cleanup
Steps:
- Create a local user.
- Sign in as that local user.
- Use Reset demo data.
- Try signing in again with the local user's credentials.
- Sign in as seeded Maya with maya@example.com / demo123.
Pass criteria:
- Reset restores original seed.
- Locally created users are removed or clearly reset according to app behavior.
- If current user was removed, app signs out cleanly.
- Seeded credentials work after reset.

Golden path smoke test:
Run this at the end:
1. Reset demo data.
2. Browse Explore signed out.
3. Open `/events/e_upcoming_open`.
4. Click RSVP signed out.
5. Sign in as Maya with maya@example.com / demo123.
6. Confirm return to event.
7. RSVP and view ticket.
8. Click Add to Calendar.
9. Sign out and sign in as Alex with alex@example.com / demo123.
10. Open My Events -> Check-in.
11. Enter Maya's ticket code.
12. Confirm counters update.
13. Enter same code again.
14. Confirm duplicate is blocked.
15. Undo last scan.
16. Confirm counters roll back.

Golden path passes only if no hidden setup, manual route recovery, or one-click mock login is required.

task.md coverage checklist:
- Host self-serve registration, profile fields, and public Host page: scenarios 14 and 25.
- Event creation fields, Draft/Published, Public/Unlisted, Publish/Unpublish/Duplicate, Free/Paid disabled: scenarios 7, 14, and 15.
- Explore filters, public browsing, past events, and social metadata: scenarios 6, 7, and 25.
- Sign-in/sign-up, RSVP redirect, ticket, QR, calendar, ticket ownership, cancellation, My Tickets: scenarios 2 through 12A.
- Capacity enforcement and FIFO waitlist promotion: scenarios 11, 12, 12A, and 13.
- Host/Checker roles, role invites, Host permissions, Checker limitations: scenarios 17, 18, and 19.
- Host Dashboard stats and CSV export: scenarios 16 and 16A.
- Check-in counters, duplicate prevention, manual code entry, and undo: scenarios 20 and 21.
- Feedback, gallery approval, any-user reporting, review queue, and hiding: scenarios 22, 23, and 24.
- Submission artifacts and seeded deployment requirements: scenario 26.

Lovable bug prompt template for failures:

Fix only this issue in GatherPass. Do not redesign unrelated screens, replace the localStorage architecture, introduce backend services, or change working flows.

Failed Atlas UI test:
- Scenario:
- Route tested:
- Account used:
- Starting state:
- Steps to reproduce:
- Expected behavior:
- Actual behavior:
- Refresh persistence result:

Acceptance test:
- Starting from [route], signed in as [user], when I [action], the app should [result].
- Refresh the page and verify the result persists where relevant.

Make the smallest reliable fix and add clear visible success/error feedback where relevant.
```
