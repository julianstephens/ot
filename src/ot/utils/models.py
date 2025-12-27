from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import msgspec

from .constants import STATE_VERSION


class RichHelpPanel(StrEnum):
    COMMITMENT_MANAGEMENT = "Commitment Management"
    COMPLETION = "Completion Commands"
    REPORTING = "Reporting Commands"


class Status(StrEnum):
    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"
    NULL = "-"


StrictModeCompleteStatuses = [Status.DONE, Status.SKIPPED]


class StrictModeRules(StrEnum):
    FORBID_FUTURE_DATES = "forbid_future_dates"
    FORBID_MODIFYING_COMPLETE_DAYS = "forbid_modifying_complete_days"
    FORBID_MULTIPLE_STATUS_FLIPS_PER_DAY = "forbid_multiple_status_flips_per_day"


class Remedy(StrEnum):
    INIT_STORAGE = "init_storage"
    FORCE_INIT_STORAGE = "force_init_storage"
    LOAD_STATE = "load_state"
    MIGRATE_STATE = "migrate_state"


@dataclass
class Day:
    title: str
    status: Status = Status.PENDING
    note: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    skipped_at: datetime | None = None


@dataclass
class Settings:
    auto_prompt_on_empty: bool = True
    strict_mode: bool = True
    default_log_days: int = 7
    max_backup_files: int = 5


SETTINGS_FIELDS = [field.name for field in fields(Settings)]
SettingsKeys = StrEnum(
    "SettingsKeys", {field.upper(): field for field in SETTINGS_FIELDS}
)


@dataclass
class DoctorResult:
    exit_code: int = 0
    autofixed: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    backup_path: Path | None = None
    remedy: Remedy | None = None

    @property
    def has_issues(self) -> bool:
        return bool(self.autofixed or self.unresolved)

    def generate_report(self) -> str:
        lines: list[str] = []

        # Header
        lines.append("State file checked.")
        lines.append("")

        # Auto-fixes
        if self.autofixed:
            lines.append("Auto-fixed:")
            lines.extend(f"- {item}" for item in self.autofixed)
        else:
            lines.append("No auto-fixes applied.")

        lines.append("")

        # Unresolved issues
        if self.unresolved:
            lines.append("Unresolved issues:")
            lines.extend(f"- {item}" for item in self.unresolved)
        else:
            lines.append("No unresolved issues.")

        lines.append("")

        # Backup information
        if self.backup_path:
            lines.append("Backup created at:")
            lines.append(str(self.backup_path))
            lines.append("")

        # Remedy / manual intervention
        if self.remedy:
            lines.append(
                "Manual intervention required. No destructive changes applied. "
                f"(Remediation code: {self.remedy.value})"
            )
        else:
            lines.append("No manual intervention needed.")

        lines.append("")
        lines.append(f"Exit code: {self.exit_code}")

        return "\n".join(lines)


class State(msgspec.Struct):
    timezone: str | None = None
    days: dict[str, Day] | None = None
    version: int = STATE_VERSION
    settings: Settings | None = None
