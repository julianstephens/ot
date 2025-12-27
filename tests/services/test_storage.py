import logging
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import msgspec
import pytest

from ot.services.storage import StorageService
from ot.utils import (
    Day,
    DayCollisionError,
    DayDoneError,
    DayUnsetError,
    Settings,
    Status,
    StorageAlreadyInitializedError,
    StorageNotInitializedError,
    StrictModeViolationError,
)


@pytest.fixture
def temp_storage_path(tmp_path):
    return tmp_path / "state.json"


@pytest.fixture
def storage_service(temp_storage_path, mocker):
    mocker.patch("ot.services.storage.CACHE_DIR", temp_storage_path.parent)
    mocker.patch("ot.services.storage.STATE_FILE", temp_storage_path.name)
    service = StorageService(lazy_load=False, log_level=logging.DEBUG)
    yield service


def test_initialize_new_storage(storage_service, temp_storage_path):
    storage_service.initialize()
    assert temp_storage_path.exists()
    assert storage_service.ready
    assert storage_service.days == {}


def test_initialize_existing_storage_raises(storage_service, temp_storage_path):
    storage_service.initialize()
    with pytest.raises(StorageAlreadyInitializedError):
        storage_service.initialize()


def test_initialize_force(storage_service, temp_storage_path):
    storage_service.initialize()
    # Modify state to verify it gets reset
    storage_service.add_day(Day(title="test"))
    assert len(storage_service.days) == 1

    storage_service.initialize(force=True)
    assert len(storage_service.days) == 0


def test_add_day(storage_service):
    storage_service.initialize()
    day = Day(title="test commitment")
    storage_service.add_day(day, date="2023-01-01")

    assert "2023-01-01" in storage_service.days
    assert storage_service.days["2023-01-01"].title == "test commitment"


def test_add_day_collision(storage_service):
    storage_service.initialize()
    day = Day(title="test")
    storage_service.add_day(day, date="2023-01-01")

    with pytest.raises(DayCollisionError):
        storage_service.add_day(day, date="2023-01-01")


def test_add_day_force(storage_service):
    storage_service.initialize()
    day1 = Day(title="test1")
    storage_service.add_day(day1, date="2023-01-01")

    day2 = Day(title="test2")
    storage_service.add_day(day2, date="2023-01-01", force=True)

    assert storage_service.days["2023-01-01"].title == "test2"


def test_get_day(storage_service):
    storage_service.initialize()
    day = Day(title="test")
    storage_service.add_day(day, date="2023-01-01")

    date, retrieved_day = storage_service.get_day("2023-01-01")
    assert date == "2023-01-01"
    assert retrieved_day.title == "test"


def test_get_day_not_found(storage_service):
    storage_service.initialize()
    date, retrieved_day = storage_service.get_day("2023-01-01")
    assert date == "2023-01-01"
    assert retrieved_day is None


def test_complete_day(storage_service):
    storage_service.initialize()
    day = Day(title="test")
    storage_service.add_day(day, date="2023-01-01")

    _, completed_day = storage_service.complete_day("2023-01-01")
    assert completed_day.status == Status.DONE
    assert completed_day.completed_at is not None


def test_complete_day_skipped(storage_service):
    storage_service.initialize()
    day = Day(title="test")
    storage_service.add_day(day, date="2023-01-01")

    _, skipped_day = storage_service.complete_day("2023-01-01", skipped=True)
    assert skipped_day.status == Status.SKIPPED
    assert skipped_day.skipped_at is not None


def test_complete_day_unset(storage_service):
    storage_service.initialize()
    with pytest.raises(DayUnsetError):
        storage_service.complete_day("2023-01-01")


def test_complete_day_already_done(storage_service):
    storage_service.initialize()

    # Disable strict mode to test DayDoneError logic
    settings = storage_service.settings
    settings.strict_mode = False
    storage_service.modify_settings(settings)

    day = Day(title="test")
    storage_service.add_day(day, date="2023-01-01")
    storage_service.complete_day("2023-01-01")

    with pytest.raises(DayDoneError):
        storage_service.complete_day("2023-01-01")


def test_add_note(storage_service):
    storage_service.initialize()
    day = Day(title="test")
    storage_service.add_day(day, date="2023-01-01")

    storage_service.add_note("test note", date="2023-01-01")
    assert storage_service.days["2023-01-01"].note == "test note"


def test_add_note_unset(storage_service):
    storage_service.initialize()
    with pytest.raises(DayUnsetError):
        storage_service.add_note("test note", date="2023-01-01")


def test_modify_settings(storage_service):
    storage_service.initialize()
    new_settings = Settings(strict_mode=True)
    storage_service.modify_settings(new_settings)

    assert storage_service.settings.strict_mode is True


def test_strict_mode_future_date(storage_service):
    storage_service.initialize()
    storage_service.modify_settings(Settings(strict_mode=True))

    # Calculate a future date
    future_year = datetime.now().year + 1
    future_date = f"{future_year}-01-01"

    day = Day(title="test")
    with pytest.raises(StrictModeViolationError):
        storage_service.add_day(day, date=future_date)


def test_get_month_days(storage_service):
    storage_service.initialize()
    storage_service.add_day(Day(title="d1"), date="2023-01-01")
    storage_service.add_day(Day(title="d2"), date="2023-01-15")

    month_days = storage_service.get_month_days("2023-01")
    assert len(month_days) == 31
    assert month_days["2023-01-01"].title == "d1"
    assert month_days["2023-01-15"].title == "d2"
    assert month_days["2023-01-02"].status == Status.NULL


def test_not_initialized_access(storage_service):
    # Don't initialize
    with pytest.raises(StorageNotInitializedError):
        _ = storage_service.days


def test_persistence(temp_storage_path, mocker):
    mocker.patch("ot.services.storage.CACHE_DIR", temp_storage_path.parent)
    mocker.patch("ot.services.storage.STATE_FILE", temp_storage_path.name)
    service1 = StorageService(lazy_load=False, log_level=logging.DEBUG)
    service1.initialize()
    service1.add_day(Day(title="persistent"), date="2023-01-01")

    # Test: load from existing file
    mocker.patch("ot.services.storage.CACHE_DIR", temp_storage_path.parent)
    mocker.patch("ot.services.storage.STATE_FILE", temp_storage_path.name)
    service2 = StorageService(lazy_load=True, log_level=logging.DEBUG)
    assert service2.days["2023-01-01"].title == "persistent"


def test_migration_v1_to_current(temp_storage_path, mocker):
    # Manually create a v1 state file
    @dataclass
    class DayV1:
        title: str
        status: Status
        note: str | None = None
        created_at: datetime | None = None
        completed_at: datetime | None = None
        skipped_at: datetime | None = None

    class StateV1(msgspec.Struct):
        timezone: str
        days: dict[str, DayV1]
        version: int = 1

    state_v1 = StateV1(
        timezone="UTC",
        days={
            "2023-01-01": DayV1(
                title="old", status=Status.PENDING, created_at=datetime.now()
            )
        },
    )

    temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_storage_path, "wb") as f:
        f.write(msgspec.json.encode(state_v1))

    mocker.patch("ot.services.storage.CACHE_DIR", temp_storage_path.parent)
    mocker.patch("ot.services.storage.STATE_FILE", temp_storage_path.name)
    service = StorageService(lazy_load=True, log_level=logging.DEBUG)
    # Accessing days should trigger load and migration
    assert service.days["2023-01-01"].title == "old"
    # Check if settings were added (part of migration)
    assert service.settings is not None


def test_strict_mode_modify_completed_day(storage_service):
    storage_service.initialize()
    storage_service.modify_settings(Settings(strict_mode=True))

    # Add and complete a day
    storage_service.add_day(Day(title="test"), date="2023-01-01")
    storage_service.complete_day("2023-01-01")

    # Try to add a note
    with pytest.raises(StrictModeViolationError):
        storage_service.add_note("new note", date="2023-01-01")


def test_strict_mode_status_flip(storage_service):
    storage_service.initialize()
    storage_service.modify_settings(Settings(strict_mode=True))

    tz = ZoneInfo(storage_service.tz)
    today = datetime.now(tz).strftime("%Y-%m-%d")

    storage_service.add_day(Day(title="test"), date=today)

    storage_service.complete_day(today)

    with pytest.raises(StrictModeViolationError):
        storage_service.complete_day(today, skipped=True)


def test_strict_mode_allowed_actions(storage_service):
    storage_service.initialize()
    storage_service.modify_settings(Settings(strict_mode=True))

    # Add day for today (allowed)
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(storage_service.tz)
    today = datetime.now(tz).strftime("%Y-%m-%d")

    storage_service.add_day(Day(title="test"), date=today)

    # Add note to incomplete day (allowed)
    storage_service.add_note("note", date=today)

    # Complete day (allowed first time)
    storage_service.complete_day(today)
