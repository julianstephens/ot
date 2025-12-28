import logging
from datetime import datetime
from pathlib import Path

import msgspec
import pytest
from freezegun import freeze_time
from tzlocal import get_localzone

from ot.services import DoctorService
from ot.utils import (
    STATE_VERSION,
    Remedy,
    State,
    Status,
)


@pytest.fixture
def mock_state_path(tmp_path):
    return tmp_path / "state.json"


@pytest.fixture
def mock_backup_dir(tmp_path):
    return tmp_path / "backups"


@pytest.fixture
def doctor_service(mock_state_path, mock_backup_dir):
    return DoctorService(mock_state_path, mock_backup_dir, log_level=logging.DEBUG)


def create_state_file(path: Path, content: dict | None = None):
    if content is None:
        content = {
            "version": STATE_VERSION,
            "timezone": "UTC",
            "settings": {
                "auto_prompt_on_empty": True,
                "strict_mode": True,
                "default_log_days": 7,
            },
            "days": {},
        }
    with path.open("wb") as f:
        f.write(msgspec.json.encode(content))


def test_doctor_missing_file(doctor_service, mock_state_path):
    """Test doctor behavior when state file is missing."""
    result = doctor_service.run()

    assert result.exit_code == 3
    assert result.remedy == Remedy.INIT_STORAGE
    assert not mock_state_path.exists()


def test_doctor_empty_file(doctor_service, mock_state_path):
    """Test doctor behavior when state file is empty."""
    mock_state_path.touch()
    result = doctor_service.run()

    assert result.exit_code == 1
    assert result.remedy == Remedy.LOAD_STATE


def test_doctor_invalid_json(doctor_service, mock_state_path):
    """Test doctor behavior when state file contains invalid JSON."""
    mock_state_path.write_text("{invalid json")
    result = doctor_service.run()

    assert result.exit_code == 2
    assert result.remedy == Remedy.FORCE_INIT_STORAGE
    assert len(result.unresolved) > 0
    assert "Decode error" in result.unresolved[0]


def test_doctor_clean_file(doctor_service, mock_state_path):
    """Test doctor behavior with a clean state file."""
    create_state_file(mock_state_path)
    result = doctor_service.run()

    assert result.exit_code == 0
    assert result.remedy is None
    assert len(result.autofixed) == 0
    assert len(result.unresolved) == 0
    assert result.backup_path is None


def test_doctor_outdated_version(doctor_service, mock_state_path):
    """Test doctor behavior with an outdated state version."""
    create_state_file(mock_state_path, {"version": 1, "days": {}})
    result = doctor_service.run()

    assert result.exit_code == 1
    assert result.remedy == Remedy.MIGRATE_STATE
    assert len(result.unresolved) > 0
    assert "migration needed" in result.unresolved[0]


def test_doctor_missing_settings(doctor_service, mock_state_path):
    """Test doctor repairs missing settings."""
    content = {
        "version": STATE_VERSION,
        "timezone": "UTC",
        "days": {},
    }
    create_state_file(mock_state_path, content)
    freeze_at = datetime(2025, 1, 1, 12, 0, 0)
    td = get_localzone().utcoffset(freeze_at)
    skip_tz_assert = False
    if not td:
        skip_tz_assert = True
    with freeze_time(freeze_at.strftime("%Y-%m-%d %H:%M:%S")):
        result = doctor_service.run()

    assert result.exit_code == 0
    assert len(result.autofixed) > 0
    assert "Settings field was missing" in result.autofixed[0]
    assert result.backup_path is not None
    if not skip_tz_assert and td is not None:
        assert (
            result.backup_path.name
            == f"state-{(freeze_at + td).strftime('%Y%m%d%H%M%S')}.json"
        )

    # Verify file content
    with mock_state_path.open("rb") as f:
        data = msgspec.json.decode(f.read(), type=State)
    assert data.settings is not None
    assert data.settings.auto_prompt_on_empty is True


def test_doctor_missing_timezone(doctor_service, mock_state_path):
    """Test doctor repairs missing timezone."""
    content = {
        "version": STATE_VERSION,
        "settings": {},
        "days": {},
    }
    create_state_file(mock_state_path, content)

    result = doctor_service.run()

    assert result.exit_code == 0
    assert any("timezone field was missing" in fix for fix in result.autofixed)

    with mock_state_path.open("rb") as f:
        data = msgspec.json.decode(f.read(), type=State)
    assert data.timezone is not None


def test_doctor_repair_days(doctor_service, mock_state_path):
    """Test doctor repairs various day issues."""
    content = {
        "version": STATE_VERSION,
        "timezone": "UTC",
        "settings": {},
        "days": {
            "2025-01-01": {"title": "Valid Day", "status": "pending"},
            "2025-01-02": {
                "title": "Invalid Status",
                "status": "INVALID",  # Should be unresolved
            },
            "2025-01-03": {
                "title": "Wrong Case",
                "status": "DONE",  # Should be fixed to "done"
            },
            "2025-01-04": {
                "title": "Missing Timestamps",
                "status": "done",  # Should add completed_at=None
            },
            "2025-01-05": {"title": "Trailing Spaces ", "status": "pending"},
            "invalid-date": {"title": "Bad Date Key", "status": "pending"},
        },
    }
    create_state_file(mock_state_path, content)

    result = doctor_service.run()

    assert result.exit_code == 0

    # Check fixes
    fixes = "\n".join(result.autofixed)
    assert "Corrected status for date '2025-01-03'" in fixes
    assert "Set completed_at for DONE day on '2025-01-04'" in fixes
    assert "Trimmed trailing spaces from title for day on '2025-01-05'" in fixes
    assert "Removed day with invalid date string 'invalid-date'" in fixes

    # Check unresolved
    unresolved = "\n".join(result.unresolved)
    assert "Invalid status 'INVALID' for date '2025-01-02'" in unresolved

    # Verify file content
    with mock_state_path.open("rb") as f:
        data = msgspec.json.decode(f.read(), type=State)

    assert data.days is not None
    assert data.days["2025-01-03"].status == Status.DONE
    assert data.days["2025-01-04"].completed_at is None
    assert data.days["2025-01-05"].title == "Trailing Spaces"
    assert "invalid-date" not in data.days


def test_doctor_backup_creation(doctor_service, mock_state_path, mock_backup_dir):
    """Test that backups are created before modification."""
    content = {
        "version": STATE_VERSION,
        "timezone": "UTC",
        "settings": {},
        "days": {},
    }
    # Missing settings will trigger a fix
    content.pop("settings")
    create_state_file(mock_state_path, content)

    result = doctor_service.run()

    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert mock_backup_dir.exists()

    # Verify backup content matches original
    with result.backup_path.open("rb") as f:
        backup_data = msgspec.json.decode(f.read())
    assert "settings" not in backup_data


def test_doctor_unfixable_issues(doctor_service, mock_state_path):
    """Test reporting of unfixable issues."""
    content = {
        "version": STATE_VERSION,
        "timezone": "UTC",
        "settings": {},
        "days": {
            "2025-01-01": {
                # Missing title
                "status": "pending"
            }
        },
    }

    content["days"]["2025-01-01"]["title"] = ""
    create_state_file(mock_state_path, content)

    result = doctor_service.run()

    assert len(result.unresolved) > 0
    assert "missing a title" in result.unresolved[0]
