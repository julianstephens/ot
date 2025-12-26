import calendar
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from zoneinfo import ZoneInfo

import msgspec
from tzlocal import get_localzone

from ot.utils import (
    CACHE_DIR,
    DATE_FORMAT,
    STATE_FILE,
    STATE_VERSION,
    DayCollisionError,
    DayDoneError,
    DayUnsetError,
    Logger,
    StorageAlreadyInitializedError,
    StorageNotInitializedError,
    get_logger,
)


class Status(StrEnum):
    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"
    NULL = "-"


@dataclass
class Day:
    title: str
    status: Status = Status.PENDING
    completed_at: datetime | None = None
    skipped_at: datetime | None = None


class State(msgspec.Struct):
    timezone: str
    days: dict[str, Day]
    version: int = STATE_VERSION


class StorageService:
    __lazy_load: bool
    __state_path: Path
    __state: State | None = None
    __state_loaded = False

    def __init__(self, lazy_load: bool):
        self.__lazy_load = lazy_load
        self.__logger = Logger("ot::StorageService", level=get_logger().level)
        self.__state_path = CACHE_DIR / STATE_FILE

    def initialize(self, force: bool = False):
        """Initialize the storage service.

        Args:
            force (bool, optional): Whether to force re-initialization if state already exists. Defaults to False.

        Raises:
            StorageAlreadyInitializedError: If the storage is already initialized and force is False.
        """
        self.__logger.info(f"using storage state path: {self.__state_path!s}")
        if self.__state_path.exists():
            self.__logger.debug("state already exists")
            if force:
                self.__logger.debug("force mode. unlinking existing state")
                self.__state_path.unlink()
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
    def tz(self) -> str:
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError
        return self.__state.timezone

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

    def add_day(self, data: Day, date: str | None = None, force: bool = False):
        """Add a day data for a specific date.

        Args:
            data (Day): The day data to add.
            date (str | None, optional): The date in YYYY-MM-DD format. Defaults to today if unset.
            force (bool, optional): Whether to force overwrite if a commitment already exists for the date. Defaults to False.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
            DayCollisionError: If a commitment already exists for the date and force is not set.
        """
        if not self.ready:
            if self.__lazy_load:
                self._load_state()
            else:
                raise StorageNotInitializedError
        assert self.__state is not None, StorageNotInitializedError

        today = (
            datetime.now(tz=ZoneInfo(self.__state.timezone)).strftime(DATE_FORMAT)
            if date is None
            else date
        )

        if today in self.__state.days and not force:
            raise DayCollisionError
        else:
            self.__state.days[today] = data

        self.__logger.debug(f"adding day data for date: {today}")
        self._save_state()

    def get_day(self, date: str | None = None) -> tuple[str, Day | None]:
        """Get the day data for a specific date.

        Args:
            date (str | None): The date in YYYY-MM-DD format. Defaults to today if unset.
        Raises:
            StorageNotInitializedError: If the storage is not initialized.
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
            date (str | None): The date in YYYY-MM-DD format. Defaults to today if unset.
            skipped (bool, optional): Whether the commitment was skipped. Defaults to False.

        Raises:
            StorageNotInitializedError: If the storage is not initialized.
            DayUnsetError: If the day is not set for the given date.
            DayDoneError: If the day is already marked as done.
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
                    title="(no commitment)", status=Status.NULL
                )
            else:
                filtered_days[day_str] = day

        return filtered_days


_storage_instance: StorageService | None = None


def get_storage(lazy_load: bool | None = None) -> StorageService:
    """Get the singleton instance of the StorageService.

    Args:
        lazy_load (bool | None, optional): Whether to lazy load the storage. Defaults to True if unset.
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageService(
            lazy_load=lazy_load if lazy_load is not None else True
        )
    return _storage_instance
