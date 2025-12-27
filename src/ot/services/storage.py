import calendar
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import msgspec
from tzlocal import get_localzone

from ot.utils import (
    CACHE_DIR,
    DATE_FORMAT,
    STATE_FILE,
    STATE_VERSION,
    Day,
    DayCollisionError,
    DayDoneError,
    DayUnsetError,
    Logger,
    Settings,
    State,
    Status,
    StorageAlreadyInitializedError,
    StorageNotInitializedError,
    StrictModeRules,
    StrictModeViolationError,
)
from ot.utils.models import StrictModeCompleteStatuses


class StorageService:
    __lazy_load: bool
    __state_path: Path
    __state: State | None = None
    __state_loaded = False

    def __init__(self, lazy_load: bool, log_level: int):
        self.__lazy_load = lazy_load
        self.__logger = Logger("ot::StorageService", level=log_level)
        self.__state_path = CACHE_DIR / STATE_FILE

    def initialize(self, force: bool = False):
        """Initialize the storage service.

        Args:
            force (bool, optional): Whether to force re-initialization if state already
                exists. Defaults to False.

        Raises:
            StorageAlreadyInitializedError: If the storage is already initialized and
                force is False.
        """
        self.__logger.info(
            f"using storage state path: {self.__state_path!s}",
        )
        if self.__state_path.exists():
            self.__logger.debug("state already exists")
            if force:
                self.__logger.debug("force mode. unlinking existing state")
                self.__state_path.unlink()
                self.__state = None
                self.__state_loaded = False
            else:
                raise StorageAlreadyInitializedError

        self.__logger.debug("ensuring state path exists...")
        self.__state_path.parent.mkdir(parents=True, exist_ok=True)
        self.__state_path.touch(exist_ok=True)
        self.__logger.debug("state path ready")

        if not self.__lazy_load:
            self.__logger.debug("lazy load disabled, loading state...")
            self._load_state()
            self.__logger.debug("state loaded")

    @property
    def ready(self) -> bool:
        """Check if the storage is ready (initialized and loaded)."""
        return self.__state is not None and self.__state_loaded

    @property
    def days(self):
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError
        return self.__state.days

    @property
    def settings(self) -> Settings:
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError
        return self.__state.settings

    @property
    def tz(self) -> str:
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError
        return self.__state.timezone

    def _migrate_state(self):
        """Migrate the state to the latest version.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
        """
        if not self.ready:
            raise StorageNotInitializedError

        self.__logger.debug("migrating state...")
        assert self.__state is not None, StorageNotInitializedError

        if self.__state.version < STATE_VERSION:
            self.__logger.debug(
                f"state version {self.__state.version} is older than"
                f" current version {STATE_VERSION}, migrating..."
            )
            if self.__state.version == 1:
                self.__logger.debug(f"migrating from version 1 to {STATE_VERSION}...")
                self.__state.settings = (
                    Settings()
                    if not hasattr(self.__state, "settings")
                    else self.__state.settings
                )
                for date, day in self.__state.days.items():
                    updated_day = Day(
                        title=day.title,
                        status=day.status,
                        note=day.note if hasattr(day, "note") else None,
                        created_at=day.created_at
                        if hasattr(day, "created_at")
                        else None,
                        completed_at=day.completed_at
                        if hasattr(day, "completed_at")
                        else None,
                        skipped_at=day.skipped_at
                        if hasattr(day, "skipped_at")
                        else None,
                    )
                    self.__state.days[date] = updated_day
                self.__logger.debug(f"migration to version {STATE_VERSION} complete")
            self.__state.version = STATE_VERSION
            self.__logger.debug("state migrated")
        else:
            self.__logger.debug("state is up to date, no migration needed")

    def _load_state(self):
        """Load the state from the storage file.

        Raises:
            StorageAlreadyInitializedError: If the storage is already initialized.
        """
        if self.ready:
            raise StorageAlreadyInitializedError

        self.__logger.debug("loading state from file...")
        data = None
        with self.__state_path.open("rb") as f:
            data = f.read()

        self.__logger.debug("decoding state...")
        if data:
            self.__logger.debug("data found, decoding...")
            self.__state = msgspec.json.decode(data, type=State)
            self.__logger.debug("state decoded")
        else:
            self.__logger.debug("no data found, initializing new state...")
            iana_timezone = get_localzone()
            self.__state = State(timezone=str(iana_timezone), days={})
            self.__logger.debug("new state initialized")

        self.__state_loaded = True
        self.__logger.debug("state loaded")
        self._migrate_state()
        self._save_state()

    def _save_state(self):
        """Save the current state to the storage file.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
        """
        if not self.ready:
            raise StorageNotInitializedError

        with self.__state_path.open("wb") as f:
            self.__logger.debug("encoding state to file...")
            f.write(msgspec.json.encode(self.__state))
            self.__logger.debug("state saved to file")

    def __enforce_strict_mode(
        self, date: str, action: Literal["add", "modify", "status"]
    ):
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        now = datetime.now(tz=ZoneInfo(self.__state.timezone))
        if self.__state.settings.strict_mode:
            match action:
                case "add":
                    self.__logger.debug("strict mode enabled, validating date...")
                    dt = datetime.strptime(date, DATE_FORMAT).replace(
                        tzinfo=ZoneInfo(self.__state.timezone)
                    )
                    if dt > now + timedelta(days=1):
                        self.__logger.debug(
                            "date is in the future, raising violation error"
                        )
                        raise StrictModeViolationError(
                            StrictModeRules.FORBID_FUTURE_DATES
                        )
                case "modify":
                    self.__logger.debug(
                        "strict mode enabled, validating modification..."
                    )
                    day = self.__state.days.get(date, None)
                    if day is not None and day.status in StrictModeCompleteStatuses:
                        self.__logger.debug(
                            "day is already completed, raising violation error"
                        )
                        raise StrictModeViolationError(
                            StrictModeRules.FORBID_MODIFYING_COMPLETE_DAYS
                        )
                case "status":
                    self.__logger.debug(
                        "strict mode enabled, validating status change..."
                    )
                    day = self.__state.days.get(date, None)
                    if day is not None:
                        if (
                            day.skipped_at is not None
                            and day.skipped_at.date() == now.date()
                        ) or (
                            day.completed_at is not None
                            and day.completed_at.date() == now.date()
                        ):
                            self.__logger.debug(
                                "day status already flipped today, raising violation"
                                " error"
                            )
                            raise StrictModeViolationError(
                                StrictModeRules.FORBID_MULTIPLE_STATUS_FLIPS_PER_DAY
                            )
        else:
            self.__logger.debug("strict mode disabled, skipping validation")

    def add_day(self, data: Day, date: str | None = None, force: bool = False) -> Day:
        """Add a day data for a specific date.

        Args:
            data (Day): The day data to add.
            date (str | None, optional): The date in YYYY-MM-DD format. Defaults to
                today if unset.
            force (bool, optional): Whether to force overwrite if a commitment already
                exists for the date. Defaults to False.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
            DayCollisionError: If a commitment already exists for the date and force is
                not set.

        Returns:
            Day: The added day data.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        now = datetime.now(tz=ZoneInfo(self.__state.timezone))
        data.created_at = now
        date = now.strftime(DATE_FORMAT) if date is None else date

        self.__enforce_strict_mode(date, action="add")

        if date in self.__state.days and not force:
            raise DayCollisionError
        else:
            self.__state.days[date] = data

        self.__logger.debug(f"adding day data for date: {date}")
        self._save_state()

        return data

    def add_note(self, message: str, date: str | None = None):
        """Add a note to a specific date.

        Args:
            message (str): The note message to add.
            date (str | None, optional): The date in YYYY-MM-DD format. Defaults to
                today if unset.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
            DayUnsetError: If the day is not set for the given date.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        date = (
            datetime.now(tz=ZoneInfo(self.__state.timezone)).strftime(DATE_FORMAT)
            if date is None
            else date
        )

        self.__enforce_strict_mode(date, action="modify")

        self.__logger.debug(f"adding note to date: {date}")
        day = self.__state.days.get(date, None)
        if day is None:
            raise DayUnsetError
        day.note = message.strip()
        self._save_state()

    def modify_day(self, new_title: str, date: str | None = None) -> tuple[str, Day]:
        """Modify the title of a day for a specific date.

        Args:
            new_title (str): The new title for the day.
            date (str | None, optional): The date in YYYY-MM-DD format.
                Defaults to today if unset.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
            DayUnsetError: If the day is not set for the given date.

        Returns:
            tuple[str, Day]: The date and the modified Day data.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        self.__logger.debug(f"modifying day for date: {date if date else 'today'}")
        date = (
            datetime.now(tz=ZoneInfo(self.__state.timezone)).strftime(DATE_FORMAT)
            if date is None
            else date
        )
        self.__enforce_strict_mode(date, action="modify")
        day = self.__state.days.get(date, None)
        if day is None:
            self.__logger.debug("no day set for this date, raising error")
            raise DayUnsetError
        day.title = new_title.strip()
        self._save_state()
        self.__logger.debug("day modified")
        return date, day

    def modify_settings(self, settings: Settings):
        """Modify the storage settings.

        Args:
            settings (Settings): The new settings to apply.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        self.__logger.debug("modifying storage settings...")
        self.__state.settings = settings
        self._save_state()

    def get_day(self, date: str | None = None) -> tuple[str, Day | None]:
        """Get the day data for a specific date.

        Args:
            date (str | None): The date in YYYY-MM-DD format. Defaults to today if
                unset.
        Raises:
            StorageNotInitializedError: If the storage is not initialized.

        Returns:
            tuple[str, Day | None]: The date and the corresponding Day data, or None if
                not set.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError
        date = (
            datetime.now(tz=ZoneInfo(self.__state.timezone)).strftime(DATE_FORMAT)
            if date is None
            else date
        )
        self.__logger.debug(f"getting data for date: {date}")
        return date, self.__state.days.get(date, None)

    def complete_day(
        self, date: str | None = None, skipped: bool = False
    ) -> tuple[str, Day]:
        """Mark a day as done for a specific date.

        Args:
            date (str | None): The date in YYYY-MM-DD format. Defaults to today if
                unset.
            skipped (bool, optional): Whether the commitment was skipped. Defaults to
                False.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
            DayUnsetError: If the day is not set for the given date.
            DayDoneError: If the day is already marked as done.

        Returns:
            tuple[str, Day]: The date and the updated Day data.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError
        date = (
            datetime.now(tz=ZoneInfo(self.__state.timezone)).strftime(DATE_FORMAT)
            if date is None
            else date
        )

        self.__enforce_strict_mode(date, action="status")

        self.__logger.debug(f"marking day as done for date: {date}")
        day = self.__state.days.get(date, None)
        if day is None:
            self.__logger.debug("no day set for this date")
            raise DayUnsetError
        if day.status == Status.DONE:
            self.__logger.debug("day already marked as done")
            raise DayDoneError
        if skipped:
            self.__logger.debug("updating day status to SKIPPED")
            day.status = Status.SKIPPED
            day.skipped_at = datetime.now(tz=ZoneInfo(self.__state.timezone))
        else:
            self.__logger.debug("updating day status to DONE")
            day.status = Status.DONE
            day.completed_at = datetime.now(tz=ZoneInfo(self.__state.timezone))
        self._save_state()
        return date, day

    def get_month_days(self, month: str) -> dict[str, Day]:
        """Get all day data for a specific month.

        Args:
            month (str): The month in YYYY-MM format.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.

        Returns
            dict[str, Day]: A dictionary of date strings to Day data for the month.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        filtered_days = {}

        _, month_length = calendar.monthrange(
            int(month.split("-")[0]), int(month.split("-")[1])
        )

        for i in range(1, month_length + 1):
            day_str = f"{month}-{i:02d}"
            day = self.__state.days.get(day_str, None)
            if day is None:
                filtered_days[day_str] = Day(
                    title="(no commitment)",
                    created_at=datetime.now(tz=ZoneInfo(self.__state.timezone)),
                    status=Status.NULL,
                )
            else:
                filtered_days[day_str] = day

        return filtered_days


_storage_instance: StorageService | None = None


def get_storage(
    lazy_load: bool | None = None, log_level=logging.CRITICAL
) -> StorageService:
    """Get the singleton instance of the StorageService.

    Args:
        lazy_load (bool | None, optional): Whether to lazy load the storage. Defaults
            to True if unset.

    Returns:
        StorageService: The singleton instance of the StorageService.
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageService(
            lazy_load=lazy_load if lazy_load is not None else True,
            log_level=log_level,
        )
    return _storage_instance
