import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import Day, Status, StorageNotInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_nudge_not_initialized(mock_storage):
    mock_storage.get_day.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_nudge_unexpected_error(mock_storage):
    mock_storage.get_day.side_effect = Exception("Boom")

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 1
    assert "An unexpected error occurred: Boom" in result.stdout


def test_nudge_no_commitment_no_prompt(mock_storage):
    mock_storage.get_day.return_value = ("2023-01-01", None)
    mock_storage.settings.auto_prompt_on_empty = False

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 0
    assert "No commitment set for today." in result.stdout


def test_nudge_no_commitment_prompt_cancel(mock_storage, mocker):
    mock_storage.get_day.return_value = ("2023-01-01", None)
    mock_storage.settings.auto_prompt_on_empty = True

    mock_prompt = mocker.patch("ot.commands.nudge_cmd.prompt_set_commitment")
    mock_prompt.return_value = None

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 0
    assert "No commitment set for today." in result.stdout
    mock_prompt.assert_called_once_with(mock_storage)


def test_nudge_no_commitment_prompt_success(mock_storage, mocker):
    mock_storage.get_day.return_value = ("2023-01-01", None)
    mock_storage.settings.auto_prompt_on_empty = True

    day = Day(title="New Commitment", status=Status.PENDING)
    mock_prompt = mocker.patch("ot.commands.nudge_cmd.prompt_set_commitment")
    mock_prompt.return_value = day

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 0
    assert "Commitment set: New Commitment" in result.stdout
    mock_prompt.assert_called_once_with(mock_storage)


def test_nudge_pending(mock_storage):
    day = Day(title="My Task", status=Status.PENDING)
    mock_storage.get_day.return_value = ("2023-01-01", day)

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 0
    assert "Pending today: 'My Task'" in result.stdout


def test_nudge_done(mock_storage):
    day = Day(title="My Task", status=Status.DONE)
    mock_storage.get_day.return_value = ("2023-01-01", day)

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 0
    assert result.stdout == ""


def test_nudge_skipped(mock_storage):
    day = Day(title="My Task", status=Status.SKIPPED)
    mock_storage.get_day.return_value = ("2023-01-01", day)

    result = runner.invoke(app, ["nudge"])

    assert result.exit_code == 0
    assert result.stdout == ""
