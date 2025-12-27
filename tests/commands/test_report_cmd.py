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
    mock_service.tz = "UTC"
    return mock_service


def test_report_success(mock_storage, mocker):
    mock_day_done = mocker.MagicMock()
    mock_day_done.status = Status.DONE
    mock_day_done.title = "Done Task"

    mock_day_skipped = mocker.MagicMock()
    mock_day_skipped.status = Status.SKIPPED
    mock_day_skipped.title = "Skipped Task"

    mock_day_pending = mocker.MagicMock()
    mock_day_pending.status = Status.PENDING
    mock_day_pending.title = "Pending Task"

    mock_day_empty = mocker.MagicMock()
    mock_day_empty.title = "(no commitment)"

    mock_storage.get_month_days.return_value = {
        "2023-01-01": mock_day_done,
        "2023-01-02": mock_day_skipped,
        "2023-01-03": mock_day_pending,
        "2023-01-04": mock_day_empty,
    }

    result = runner.invoke(app, ["report", "--month", "2023-01"])

    assert result.exit_code == 0
    assert "Report for 2023-01" in result.stdout
    assert "Days with a commitment: 3" in result.stdout
    assert "done: 1" in result.stdout
    assert "skipped: 1" in result.stdout
    assert "pending: 1" in result.stdout
    # 1 done out of 3 commitments = 33.33%
    assert "33.33%" in result.stdout


def test_report_not_initialized(mock_storage):
    mock_storage.get_month_days.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["report", "--month", "2023-01"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_report_generic_error(mock_storage):
    mock_storage.get_month_days.side_effect = Exception("Boom")

    result = runner.invoke(app, ["report", "--month", "2023-01"])

    assert result.exit_code == 1
    assert "Failed to retrieve data for month 2023-01: Boom" in result.stdout
