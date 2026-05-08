# GatherPass Stateful UI Test Scenarios For OpenAI Atlas

This file records the browser QA scenarios used for the official stateful Lovable Cloud version of GatherPass.

Target app:
https://gather-pass-hub.lovable.app/

The scenarios are split by backend migration checkpoint because the app was easier to validate surface-by-surface than with one large browser pass. Earlier browser-state testing was useful during development, but the official repo now treats the Cloud-backed app as the submission target.

## Testing Rules

- Use visible navigation first; use direct URLs only for route-guard, Unlisted, Draft, ticket privacy, or invite-link checks.
- Prefer a fresh Atlas session when possible. If only one browser context is available, sign in/out between seeded users and use refreshes to verify shared Cloud persistence.
- Do not treat CSV content inspection as failed if Atlas can trigger the download but cannot inspect the file. Mark it `NOT VERIFIED`.
- Do not spend Lovable credits on broad fixes until Atlas identifies a concrete failing flow.
- Treat small loading shells or delayed role-link flashes as acceptable if they resolve to the correct user/role without manual route recovery.
- Public reset must remain absent because backend state is shared.

## Seeded Accounts

- `maya@example.com` / `demo123` - attendee
- `jordan@example.com` / `demo123` - Host
- `alex@example.com` / `demo123` - Checker
- `priya@example.com` / `demo123` - attendee
- `omar@example.com` / `demo123` - attendee
- `riley@example.com` / `demo123` - attendee

## Checkpoint A: Cloud Auth And Read Layer

```text
Test GatherPass as an independent reviewer.

Target app:
https://gather-pass-hub.lovable.app/

Focus only on Cloud auth and Cloud read-layer behavior. Do not test persistence for RSVP, event create/edit, check-in, invite creation, feedback submission, photo upload, or moderation in this checkpoint.

Use visible navigation first. Use direct URLs only for route-guard checks.

Verify:
1. Signed-out user can browse Explore.
2. Signed-out user can open a public event page.
3. Signed-out user can open a known Unlisted published event URL if available.
4. Draft event direct URL is blocked for signed-out/non-host users.
5. Jordan can sign in with jordan@example.com / demo123.
6. Maya can sign in with maya@example.com / demo123.
7. Alex can sign in with alex@example.com / demo123.
8. Redirect-after-sign-in works when starting from RSVP or a protected route.
9. Maya's My Tickets page loads seeded ticket/waitlist data from Cloud.
10. Jordan's Host Dashboard loads seeded Host/events/counts from Cloud.
11. Alex's My Events page loads Checker-accessible events from Cloud.
12. Public reset action is absent.
13. Footer/UI does not say data persists only in the browser.
14. Refreshing authenticated routes keeps the user signed in and reloads Cloud data.
15. Header/profile identity and role navigation update after sign-out and account switching.
16. No primary route is blank or a placeholder.

Return:
- PASS/FAIL by area.
- Browser/session setup used.
- Any route that failed.
- Any visible issue with auth, loading states, route guards, or Cloud read data.
- Do not mark write persistence as failed in this checkpoint.
```

## Checkpoint B: RSVP, Tickets, And Waitlist RPCs

```text
Test GatherPass as an independent reviewer.

Target app:
https://gather-pass-hub.lovable.app/

Focus only on backend RSVP, tickets, and waitlist behavior.

Use:
- Sunset Sketch Walk for under-capacity Going + ticket.
- Community Coding Night for full/waitlist.

Seeded accounts:
- maya@example.com / demo123
- omar@example.com / demo123
- riley@example.com / demo123
- jordan@example.com / demo123 as Host

Verify:
1. Signed-out RSVP redirects to sign-in and returns to the event page.
2. Under-capacity RSVP on Sunset succeeds.
3. Attendee becomes Going.
4. Ticket is visible.
5. Refresh preserves Going/ticket.
6. Host Dashboard counts reflect the Going RSVP after signing in as Jordan.
7. Full-event RSVP on Community Coding Night creates Waitlisted state.
8. Waitlisted attendee has no confirmed ticket.
9. Refresh preserves Waitlisted state.
10. Canceling a Going RSVP promotes the oldest Waitlisted attendee FIFO if the setup is available.
11. Draft event RSVP remains blocked/rejected.
12. Past event RSVP is hidden or rejected.
13. Ticket page remains owner-only.
14. Public reset action remains absent.
15. No route becomes blank.

Known migration gotchas to watch:
- An RSVP button can render correctly while the RPC still fails.
- Under-capacity RSVP exercises ticket generation; full-event waitlist does not.
- If under-capacity RSVP fails but waitlist works, inspect backend ticket-code generation and RPC error logs.

Return:
- PASS/FAIL by item.
- Evidence that RSVP/waitlist state persisted after refresh.
- Evidence that host counts saw backend state.
- Any blocking issue only.
```

## Checkpoint C: Host Event Editor Writes

```text
Retest only Host Event Editor write persistence.

Target app:
https://gather-pass-hub.lovable.app/

Use:
- jordan@example.com / demo123

Steps:
1. Sign in as Jordan.
2. Open Host Dashboard.
3. Click New Event.
4. Fill:
   - Title: Atlas Cloud Smoke [current time]
   - Description: Temporary Atlas smoke test event for Cloud persistence.
   - Start date: 2026-06-01
   - Start time: 18:00
   - End date: 2026-06-01
   - End time: 20:00
   - Timezone: America/Los_Angeles
   - Venue: Atlas Test Hall
   - Capacity: 12
   - Cover image URL: use the default helper if present, otherwise paste:
     https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=1200&q=70&auto=format&fit=crop
   - Visibility: Public
   - Pricing: Free
5. Save draft.
6. Refresh Host Dashboard and confirm the draft persists.
7. Open the draft and publish it.
8. Sign out, open Explore, confirm the event appears.
9. Sign in as Jordan, unpublish it.
10. Sign out, open Explore, confirm the event no longer appears.
11. Sign in as Jordan, duplicate an existing event.
12. Refresh Host Dashboard and confirm the duplicate persists as Draft.

Return PASS/FAIL only for:
- Full draft creation persists.
- Publish persists and appears in Explore.
- Unpublish persists and disappears from Explore.
- Duplicate persists as Draft.
- Any validation/input issue remaining.
```

## Checkpoint D: Remaining Backend Write Flows

```text
Continue backend write-flow testing for GatherPass.

Target app:
https://gather-pass-hub.lovable.app/

Already passed:
- RSVP/ticket/waitlist backend writes.
- Host event create/publish/unpublish/duplicate persistence.

Do not retest those except where needed for check-in.

Use seeded accounts:
- jordan@example.com / demo123 - Host
- alex@example.com / demo123 - Checker
- maya@example.com / demo123 - Attendee
- omar@example.com / demo123 - Attendee
- riley@example.com / demo123 - Attendee

Test these remaining write surfaces:

1. Capacity increase promotion
- As Jordan, open Community Coding Night if it has waitlisted users.
- Increase capacity.
- Confirm oldest waitlisted attendee is promoted FIFO and gets Going/ticket.
- Refresh and confirm promotion persists.

2. CSV export
- As Jordan, export RSVPs/attendance for an event.
- If download content is inspectable, confirm exact headers:
  name,email,RSVP status,check-in time
- If not inspectable, report NOT VERIFIED, not FAIL.

3. Check-in
- Find a valid Going ticket code.
- Sign in as Alex.
- Open My Events -> Check-in.
- Enter valid code.
- Confirm check-in succeeds and counters update.
- Refresh and confirm check-in persists.
- Enter same code again; confirm duplicate is blocked.
- Undo last check-in; refresh; confirm undo persists.
- Try invalid code; rejected.
- If available, try waitlisted/cancelled code; rejected.

4. Invites
- Sign in as Jordan.
- Create a Checker or Host invite link.
- Sign in as an attendee without that role.
- Accept invite.
- Confirm role access appears after acceptance.
- Sign out/in or refresh and confirm role persists.
- Try reusing same invite link; confirm it is rejected.

5. Feedback
- Sign in as Maya.
- Open a past event.
- Submit or update 1-5 star feedback with a short comment.
- Refresh and confirm it persists.

6. Gallery
- As attendee, add/upload a gallery photo.
- Confirm it starts Pending and is not public.
- Sign in as Jordan.
- Approve it.
- Refresh/public view confirms it appears.
- Hide it.
- Refresh/public view confirms it disappears.

7. Reports
- As attendee, report an event or photo.
- Sign in as Jordan.
- Confirm report appears in Host review queue.
- Resolve or hide it.
- Refresh and confirm moderation state persists.

8. Permissions
- Attendee cannot access Host Dashboard, check-in, or moderation.
- Checker cannot edit events, export CSV, or manage Host Dashboard.
- Public reset action remains absent.
- No primary route is blank.

Return:
- PASS/FAIL/NOT VERIFIED by item.
- For failures only: account, route, steps, expected, actual, and refresh result.
- Keep the report concise.
```

## Checkpoint E: Final Post-Security Regression

```text
Run final post-security regression QA for GatherPass.

Target app:
https://gather-pass-hub.lovable.app/

Context:
Lovable Cloud backend migration is complete. Security hardening changed RLS/function grants:
- feedback is no longer public-readable; author or event Host can read it
- invite table is not public-readable; invite acceptance uses backend RPC
- mutation RPCs are authenticated-only
- public_profiles is public-safe; profiles is owner-only
- public reset action is absent

Use visible navigation first. Use direct URLs only for route/security checks.

Seeded accounts:
- jordan@example.com / demo123 - Host
- alex@example.com / demo123 - Checker
- maya@example.com / demo123 - Attendee
- omar@example.com / demo123 - Attendee
- riley@example.com / demo123 - Attendee

Verify core flows:
1. Signed-out Explore works.
2. Signed-out public event detail works.
3. Signed-out Unlisted event direct URL works.
4. Draft event direct URL is blocked for signed-out/non-host users.
5. Jordan can still open Host Dashboard.
6. Alex can still open My Events and Check-in.
7. Maya/Omar/Riley cannot access Host Dashboard, check-in, or moderation.

Verify RSVP/tickets:
8. Under-capacity RSVP still creates Going + ticket and persists after refresh.
9. Full-event RSVP still creates Waitlisted and no confirmed ticket.
10. Ticket page is owner-only; another attendee cannot view someone else's ticket.

Verify Host/event writes:
11. Jordan can create/save a draft event with full valid fields; refresh persists.
12. Publish makes it appear in Explore; unpublish removes it.
13. Duplicate persists as Draft.
14. Capacity increase still promotes waitlist FIFO if applicable.

Verify check-in:
15. Alex can check in a valid Going ticket.
16. Duplicate check-in is blocked.
17. Undo check-in persists after refresh.
18. Invalid/waitlisted/cancelled ticket code is rejected if available.

Verify invites:
19. Jordan can create a Host or Checker invite.
20. A signed-in attendee can accept it and gain role access.
21. Reusing the same invite fails safely.
22. Invite token data is visible only to the Host for copy/share, not exposed publicly.

Verify feedback/gallery/reports after security hardening:
23. Maya can submit/update feedback on a past event; refresh persists.
24. Jordan as Host can see relevant feedback for his event.
25. Public/signed-out event pages still render correctly even if feedback is restricted.
26. Maya can add/upload a gallery photo; it starts Pending and is not public.
27. Jordan can approve it; approved photo appears publicly.
28. Jordan can hide it; hidden photo disappears publicly.
29. Maya can report an event or photo.
30. Jordan can see the report in the Host review queue after security hardening.
31. Jordan can resolve or hide the reported item; refresh persists.

Other:
32. CSV export button still triggers download. If headers cannot be inspected, mark NOT VERIFIED, not FAIL.
33. Public reset action remains absent.
34. No primary route is blank.
35. No UI says data persists only in browser.

Return:
- PASS/FAIL/NOT VERIFIED by section, not long prose.
- Any blocking issue with account, route, steps, expected, actual, refresh result.
- Note any issue caused by the new RLS/security hardening.
```

## Lovable Bug Prompt Template

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
