from dataclasses import dataclass, fields
from datetime import datetime
from enum import StrEnum

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


SETTINGS_FIELDS = [field.name for field in fields(Settings)]
SettingsKeys = StrEnum(
    "SettingsKeys", {field.upper(): field for field in SETTINGS_FIELDS}
)


class State(msgspec.Struct):
    timezone: str
    days: dict[str, Day]
    settings: Settings = Settings()
    version: int = STATE_VERSION
