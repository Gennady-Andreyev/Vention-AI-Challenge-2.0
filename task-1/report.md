# Task 1 — Report

## Approach

The goal was to replicate the internal company leaderboard exactly, including all UI elements, filters, sorting, and expand/collapse behaviour, without feeding any real personal data to an external LLM.

### Reviewing the original page

The original SharePoint leaderboard was reviewed visually in the browser. Screenshots were taken and personal information (full names, department names, and avatars/photos) was masked by drawing blue rectangles over them before sharing with Claude Code. No real names or other personal data were sent to any external LLM.

### Understanding the UI

From the masked screenshots the following elements were identified:
- A page header with title and subtitle
- A filter bar with three dropdowns (Year, Quarter, Category) and a text search input
- A top-3 podium section with visual platforms and per-person score cards
- A ranked list of employees, each row collapsible to reveal a "Recent Activity" table

Icons in each collapsed row indicate the number of activities per category:
- **Monitor** → Public Speaking (REG)
- **Graduation cap** → Education (LAB)
- **Smile** → University Partnership (UNI)

The smile icon was deduced by cross-referencing the icon counts in a rank-13 card (graduation=4, smile=3) with the visible activity entries (4 LAB + 3 UNI).

### Data replacement

All real names and department codes were replaced with mocked equivalents:
- Names use realistic Eastern European first/last names (no relation to real employees)
- Unit codes are fictional (UA01, BY03, PL07, UZ01, etc.)
- Activity descriptions were reused as-is when they contained no personal data (lecture names, event names); mentoring entries were rewritten with mocked names
- Avatars are initials-only (no photos used); background colour is deterministically derived from initials via a short hash mapped to a 5-colour pastel palette, so each person always gets the same colour

### Implementation

- **Framework:** React 18 + Vite (plain JavaScript)
- **Icons:** lucide-react (GraduationCap, Presentation, Smile, ChevronDown, ChevronUp, Search); the podium star is an inline SVG to avoid lucide's filled-star limitation
- **Styling:** plain CSS — no utility-class frameworks; design tokens scoped as CSS custom properties on `.podium`
- **Podium design:** rank-1 column uses a gold double-ring avatar (white inner border + amber outer box-shadow), an amber badge, and a warm-yellow score pill; rank-2 and rank-3 use identical gray gradient platforms to match the original screenshot; platform height decreases with rank and scales down on mobile — platforms remain visible at all breakpoints
- **Filtering logic:** `applyFilters` returns two arrays — `ranked` (full re-ranking ignoring search) and `filtered` (search applied on top). The podium is always drawn from the top 3 of `ranked` and then narrowed to only the names that match the current search term, so searching for a top-3 person still shows them on the podium rather than hiding it
- **Expand/collapse state:** row open/closed state is keyed by employee ID in a `Set`; it survives filter and search changes because the IDs are stable
- **Responsiveness:** below 900 px the podium stacks vertically (gold first, then silver, then bronze) at a fixed width; the filter bar wraps to two rows on narrow screens
- **Deployment:** gh-pages package with `--dest task-1` flag so the app lives at `/Vention-AI-Challenge-2.0/task-1/` without colliding with future tasks

## Live URL

https://gennady-andreyev.github.io/Vention-AI-Challenge-2.0/task-1/
