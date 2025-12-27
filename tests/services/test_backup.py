import logging
import time

import pytest

from ot.services import BackupService
from ot.utils import DEFAULT_MAX_BACKUP_FILES


@pytest.fixture
def backup_service(tmp_path):
    state_path = tmp_path / "state.json"
    state_path.write_text('{"test": "data"}')
    backup_dir = tmp_path / "backups"
    return BackupService(state_path, backup_dir, logging.DEBUG)


def test_init(tmp_path):
    state_path = tmp_path / "state.json"
    backup_dir = tmp_path / "backups"
    service = BackupService(state_path, backup_dir, logging.DEBUG)

    assert service.state_path == state_path
    assert service.backup_dir == backup_dir
    assert service.max_backup_files == DEFAULT_MAX_BACKUP_FILES


def test_init_custom_max_files(tmp_path):
    state_path = tmp_path / "state.json"
    backup_dir = tmp_path / "backups"
    service = BackupService(state_path, backup_dir, logging.DEBUG, max_backup_files=10)

    assert service.max_backup_files == 10


def test_set_max_backup_files(backup_service):
    backup_service.set_max_backup_files(5)
    assert backup_service.max_backup_files == 5


def test_create_backup(backup_service):
    backup_path = backup_service.create_backup()

    assert backup_path.exists()
    assert backup_path.parent == backup_service.backup_dir
    assert backup_path.name.startswith("state-")
    assert backup_path.name.endswith(".json")
    assert backup_path.read_text() == '{"test": "data"}'


def test_cleanup_old_backups(backup_service):
    # Set limit to 2
    backup_service.set_max_backup_files(2)
    backup_service.backup_dir.mkdir(parents=True, exist_ok=True)

    # Create 3 dummy backup files with different timestamps
    files = []
    for i in range(3):
        p = backup_service.backup_dir / f"state-{i}.json"
        p.touch()
        files.append(p)
        # Ensure mtime difference
        time.sleep(0.01)

    # Verify all exist
    assert len(list(backup_service.backup_dir.glob("state*.json"))) == 3

    # Run cleanup
    backup_service.cleanup_old_backups()

    # Should have 2 left (the newest ones)
    remaining = sorted(
        list(backup_service.backup_dir.glob("state*.json")),
        key=lambda f: f.stat().st_mtime,
    )
    assert len(remaining) == 2
    assert remaining[0].name == "state-1.json"
    assert remaining[1].name == "state-2.json"
    assert not (backup_service.backup_dir / "state-0.json").exists()


def test_create_backup_triggers_cleanup(backup_service, mocker):
    spy = mocker.spy(backup_service, "cleanup_old_backups")

    backup_service.create_backup()

    spy.assert_called_once()
