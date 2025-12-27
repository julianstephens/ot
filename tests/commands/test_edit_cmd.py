import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import (
    DayUnsetError,
    StorageNotInitializedError,
    StrictModeRules,
    StrictModeViolationError,
)

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_edit_success_today(mock_storage):
    mock_storage.modify_day.return_value = ("2023-01-01", None)

    result = runner.invoke(app, ["edit", "New Title"])

    assert result.exit_code == 0
    assert "Commitment for today updated to: New Title" in result.stdout
    mock_storage.modify_day.assert_called_once_with(new_title="New Title", date=None)


def test_edit_success_date(mock_storage):
    mock_storage.modify_day.return_value = ("2023-01-01", None)

    result = runner.invoke(app, ["edit", "New Title", "--date", "2023-01-01"])

    assert result.exit_code == 0
    assert "Commitment for 2023-01-01 updated to: New Title" in result.stdout
    mock_storage.modify_day.assert_called_once_with(
        new_title="New Title", date="2023-01-01"
    )


def test_edit_not_initialized(mock_storage):
    mock_storage.modify_day.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["edit", "New Title"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_edit_day_unset(mock_storage):
    mock_storage.modify_day.side_effect = DayUnsetError

    result = runner.invoke(app, ["edit", "New Title"])

    assert result.exit_code == 1
    assert "Failed to edit commitment" in result.stdout
    # DayUnsetError might not have a message, so we just check the prefix


def test_edit_strict_mode_violation(mock_storage):
    mock_storage.modify_day.side_effect = StrictModeViolationError(
        StrictModeRules.FORBID_MODIFYING_COMPLETE_DAYS
    )

    result = runner.invoke(app, ["edit", "New Title"])

    assert result.exit_code == 1
    assert (
        "Failed to edit commitment: The operation could not be completed in strict"
        in result.stdout
    )


def test_edit_generic_error(mock_storage):
    mock_storage.modify_day.side_effect = Exception("Boom")

    result = runner.invoke(app, ["edit", "New Title"])

    assert result.exit_code == 1
    assert "Failed to edit commitment: Boom" in result.stdout
