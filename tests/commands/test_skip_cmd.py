import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import DayDoneError, DayUnsetError, StorageNotInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_skip_success(mock_storage, mocker):
    mock_day = mocker.MagicMock()
    mock_day.title = "Test Commitment"
    mock_storage.complete_day.return_value = ("2023-01-01", mock_day)

    result = runner.invoke(app, ["skip"])

    assert result.exit_code == 0
    assert "Commitment for 2023-01-01 skipped: Test Commitment" in result.stdout
    mock_storage.complete_day.assert_called_once_with(date=None, skipped=True)


def test_skip_with_date(mock_storage, mocker):
    mock_day = mocker.MagicMock()
    mock_day.title = "Test Commitment"
    mock_storage.complete_day.return_value = ("2023-01-01", mock_day)

    result = runner.invoke(app, ["skip", "--date", "2023-01-01"])

    assert result.exit_code == 0
    mock_storage.complete_day.assert_called_once_with(date="2023-01-01", skipped=True)


def test_skip_not_initialized(mock_storage):
    mock_storage.complete_day.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["skip"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_skip_day_unset_no_prompt(mock_storage):
    mock_storage.complete_day.side_effect = DayUnsetError
    mock_storage.settings.auto_prompt_on_empty = False

    result = runner.invoke(app, ["skip"])

    assert result.exit_code == 0
    assert "No commitment set for today" in result.stdout


def test_skip_day_unset_prompt(mock_storage, mocker):
    mock_storage.complete_day.side_effect = DayUnsetError
    mock_storage.settings.auto_prompt_on_empty = True
    mock_prompt = mocker.patch("ot.commands.skip_cmd.prompt_set_commitment")

    result = runner.invoke(app, ["skip"])

    assert result.exit_code == 0
    mock_prompt.assert_called_once_with(mock_storage)


def test_skip_already_done(mock_storage):
    mock_storage.complete_day.side_effect = DayDoneError

    result = runner.invoke(app, ["skip"])

    assert result.exit_code == 0
    assert "Commitment for today is already marked as done" in result.stdout


def test_skip_generic_error(mock_storage):
    mock_storage.complete_day.side_effect = Exception("Boom")

    result = runner.invoke(app, ["skip"])

    assert result.exit_code == 1
    assert "Error marking commitment as skipped: Boom" in result.stdout
