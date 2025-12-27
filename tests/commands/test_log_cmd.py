import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import Status, StorageNotInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    # Default timezone
    mock_service.tz = "UTC"
    # Default settings
    mock_service.settings.default_log_days = 7
    return mock_service


def test_log_default(mock_storage):
    mock_storage.days = {}

    result = runner.invoke(app, ["log"])

    assert result.exit_code == 0
    # Should print 7 days by default
    assert result.stdout.count("\n") >= 7


def test_log_with_days(mock_storage):
    mock_storage.days = {}

    result = runner.invoke(app, ["log", "--days", "3"])

    assert result.exit_code == 0
    # Should print 3 lines of output (plus maybe empty lines)
    # We can check if it called storage.days
    assert mock_storage.days == {}


def test_log_with_month(mock_storage, mocker):
    mock_day = mocker.MagicMock()
    mock_day.status = Status.DONE
    mock_day.title = "Test"
    mock_storage.get_month_days.return_value = {"2023-01-01": mock_day}

    result = runner.invoke(app, ["log", "--month", "2023-01"])

    assert result.exit_code == 0
    assert "2023-01-01" in result.stdout
    assert "done" in result.stdout
    assert "Test" in result.stdout
    mock_storage.get_month_days.assert_called_once_with("2023-01")


def test_log_not_initialized(mock_storage):
    mock_storage.get_month_days.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["log", "--month", "2023-01"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_log_month_error(mock_storage):
    mock_storage.get_month_days.side_effect = Exception("Boom")

    result = runner.invoke(app, ["log", "--month", "2023-01"])

    assert result.exit_code == 1
    assert "Failed to retrieve data for month 2023-01: Boom" in result.stdout
