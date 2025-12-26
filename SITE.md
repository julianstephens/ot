# One Thing

CLI for choosing one non-negotiable commitment per day and tracking whether it happens

## Overview

- **Day**: A calendar date in your local timezone (`YYYY-MM-DD`).
- **Commitment**: The “one thing” chosen for a day, e.g. `"Call mom"`.
- **Status** (per day):
  - `pending` — commitment exists, not yet completed.
  - `done` — completed.
  - `skipped` — explicitly not done.

- You can have **0 or 1 commitment per day**. Never more.

---

## Storage design

Single JSON file, e.g.:

- Default path: `~/.one_thing/one_thing.json`

**Schema**

```json
{
  "version": 1,
  "timezone": "America/New_York",
  "days": {
    "2025-12-26": {
      "title": "Call mom",
      "status": "pending",
      "created_at": "2025-12-26T10:12:04-05:00",
      "completed_at": null,
      "skipped_at": null
    },
    "2025-12-25": {
      "title": "Finish seminar prep",
      "status": "done",
      "created_at": "2025-12-25T09:15:00-05:00",
      "completed_at": "2025-12-25T20:30:00-05:00",
      "skipped_at": null
    }
  }
}
```

---

## CLI interface

Binary name: `ot`

### `ot init`

**Purpose:** create the data file + directory.

**Behavior:**

- If `~/.one_thing/` doesn’t exist, create it.
- If `one_thing.json` doesn’t exist, create with:

```json
{ "version": 1, "days": {} }
```

- If it exists, warn and exit (unless `--force`).

Example:

```bash
ot init
ot init --force  # overwrites file
```

---

### `ot today`

**Purpose:** show today’s commitment and status.

**Behavior:**

- Get today’s date in local timezone.

- If there’s a commitment, print:

  ```
  2025-12-26 — pending
    Call mom
  ```

- If none:

  ```
  2025-12-26 — no commitment set
  ```

Support `--date YYYY-MM-DD` to inspect any date:

```bash
ot today          # shows today
ot today --date 2025-12-24
```

---

### `ot set "text"`

**Purpose:** set the one thing for today (or a specified date).

**Behavior:**

- Compute target date:
  - Default: today.
  - Or `--date YYYY-MM-DD`.

- If date already has a commitment and `--force` not given:
  - Print error and show existing commitment.

- If no commitment (or `--force`), set:
  - `title` = provided text.
  - `status` = `pending`.

Examples:

```bash
ot set "Call mom"
ot set --date 2025-12-28 "Finish draft of section 3"
ot set --force "Replace today's commitment with something else"
```

---

### `ot done`

**Purpose:** mark today’s commitment as completed.

**Behavior:**

- Target date = today, unless `--date` given.
- If no commitment exists:
  - Print: `No commitment set for 2025-12-26.`

- If status already `done`:
  - Print: `Already done: "<title>"`.

- Else:
  - Set `status` = `done`.
  - Optionally set `completed_at` timestamp.

Examples:

```bash
ot done
ot done --date 2025-12-25
```

---

### `ot skip`

**Purpose:** explicitly mark today’s commitment as not done.

**Behavior:**

Very similar to `done`, but sets `status` = `skipped`, `skipped_at` timestamp optional.

```bash
ot skip
ot skip --date 2025-12-24
```

---

### `ot log`

**Purpose:** show a concise list of recent days.

**Behavior:**

- Show last N days (default 7), with status and title.
- Or a month view if `--month` provided (`YYYY-MM`).

Output (recent 7):

```text
2025-12-26  pending  Call mom
2025-12-25  done     Finish seminar prep
2025-12-24  skipped  Go climbing
2025-12-23  —        (no commitment)
...
```

Examples:

```bash
ot log
ot log --days 14
ot log --month 2025-12
```

If using `--month`, you can show days in calendar order.

---

### `ot report`

**Purpose:** lightweight stats for a given month.

**Behavior:**

For a given `--month YYYY-MM` (default: current month):

- Count:
  - `total_days_with_commitment`
  - `done_count`
  - `skipped_count`
  - `pending_count`

- Print simple percentages.

Example output:

```text
Report for 2025-12

Days with a commitment: 18
  done:    12
  skipped: 3
  pending: 3

Completion rate (done / commitment days): 66.7%
```

Example usage:

```bash
ot report
ot report --month 2026-01
```