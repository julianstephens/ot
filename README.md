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
  "version": 2,
  "timezone": "America/New_York",
  "settings": {
    "prompt_on_empty": true,
    "strict_mode": false,
    "default_log_days": 7
  },
  "days": {
    "2025-12-26": {
      "title": "Call mom",
      "status": "pending",
      "note": null,
      "created_at": "2025-12-26T10:12:04-05:00",
      "completed_at": null,
      "skipped_at": null
    },
    "2025-12-25": {
      "title": "Finish seminar prep",
      "status": "done",
      "note": "Wrapped up around 8pm, felt good",
      "created_at": "2025-12-25T09:15:00-05:00",
      "completed_at": "2025-12-25T20:30:00-05:00",
      "skipped_at": null
    }
  }
}
```

---

## CLI Configuration

### Auto Prompt on Empty

Prompts user to set a commitment when they attemp to act on an unset day

### Default Log Days

The number of days displayed when inspecting commitment logs

### Strict Mode

Strict mode enforces one decision per day with limited editing

**Behavior:**

- Prevents setting more than one future day ahead
- Disallows editing after marking done/skipped
- Refuses multiple status flips per day

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

### `ot nudge`

**Purpose:** remind you of today's commitment.

**Behavior:**

- If commitment exists and is pending:
  - Print: `Pending today: '<title>'`

- If no commitment:
  - Prompt to set one (if `auto_prompt_on_empty` is enabled).

Examples:

```bash
ot nudge
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

### `ot edit "new title"`

**Purpose:** edit the title of an existing commitment.

**Behavior:**

- Target date:
  - Default: today.
  - Or `--date YYYY-MM-DD`.

- Updates the commitment title to the new text.

Examples:

```bash
ot edit "Call dad instead"
ot edit --date 2025-12-28 "Finish draft of section 4"
```

---

### `ot note`

**Purpose:** set a brief note for today (or a specified date).

**Behavior:**

- Compute target date:
  - Default: today.
  - Or `--date YYYY-MM-DD`.

- If no commitment:
  - Prompt if `settings.auto_prompt_on_empty` else print error

- Replace `note` with provided `message`

Examples:

```bash
ot note
ot note --date 2025-12-25
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

---

### `ot config view`

**Purpose:** view the current CLI configuration settings values

**Behavior:**

- Display all stored settings and current values

Example output:

```text
Current Configuration Settings:
  Default Log Days :    7
  Prompt on Empty  :    True
  Strict Mode      :    False

```

Example usage:

```bash
ot config view
```

---

### `ot config set "key"`

**Purpose:** update CLI configuration settings

**Behavior:**

- Prompt user for new setting value
- Update and save storage state

Example usage:

```bash
ot config set prompt_on_empty
ot config set strict_mode
```
