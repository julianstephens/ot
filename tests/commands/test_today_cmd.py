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


def test_today_success(mock_storage, mocker):
    mock_day = mocker.MagicMock()
    mock_day.status = Status.PENDING
    mock_day.title = "Test Commitment"
    mock_day.note = "Test Note"
    mock_storage.get_day.return_value = ("2023-01-01", mock_day)

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    assert "2023-01-01 - pending" in result.stdout
    assert "Test Commitment" in result.stdout
    assert "Test Note" in result.stdout


def test_today_with_date(mock_storage, mocker):
    mock_day = mocker.MagicMock()
    mock_day.status = Status.PENDING
    mock_day.title = "Test Commitment"
    mock_day.note = None
    mock_storage.get_day.return_value = ("2023-01-01", mock_day)

    result = runner.invoke(app, ["today", "--date", "2023-01-01"])

    assert result.exit_code == 0
    mock_storage.get_day.assert_called_once_with("2023-01-01")


def test_today_not_initialized(mock_storage):
    mock_storage.get_day.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


from datetime import datetime
from zoneinfo import ZoneInfo

from ot.utils import DATE_FORMAT


def test_today_empty_no_prompt(mock_storage, capsys):
    # Use real date to avoid patching datetime
    today_str = datetime.now(tz=ZoneInfo("UTC")).strftime(DATE_FORMAT)

    mock_storage.get_day.return_value = (today_str, None)
    mock_storage.settings.auto_prompt_on_empty = False

    result = runner.invoke(app, ["today"])

    # Check captured output from capsys?
    # CliRunner captures output too.

    print(f"STDOUT: {result.stdout}")

    assert result.exit_code == 0
    assert f"{today_str} - no commitment set" in result.stdout


def test_today_empty_prompt_success(mock_storage, mocker):
    mock_storage.get_day.return_value = ("2023-01-01", None)
    mock_storage.settings.auto_prompt_on_empty = True

    mock_day = mocker.MagicMock()
    mock_day.status = Status.PENDING
    mock_day.title = "New Commitment"
    mock_day.note = None

    mock_prompt = mocker.patch("ot.commands.today_cmd.prompt_set_commitment")
    mock_prompt.return_value = mock_day

    mock_print = mocker.patch("ot.commands.today_cmd.print")

    mock_datetime = mocker.patch("ot.commands.today_cmd.datetime")
    mock_datetime.now.return_value.strftime.return_value = "2023-01-01"

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    # Verify calls to print
    # It prints date - status, then title
    mock_print.assert_any_call("2023-01-01 - pending")
    mock_print.assert_any_call("  New Commitment")


def test_today_empty_prompt_none(mock_storage, mocker):
    mock_storage.get_day.return_value = ("2023-01-01", None)
    mock_storage.settings.auto_prompt_on_empty = True

    mock_prompt = mocker.patch("ot.commands.today_cmd.prompt_set_commitment")
    mock_prompt.return_value = None

    mock_print = mocker.patch("ot.commands.today_cmd.print")

    mock_datetime = mocker.patch("ot.commands.today_cmd.datetime")
    mock_datetime.now.return_value.strftime.return_value = "2023-01-01"

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    mock_print.assert_called_with("2023-01-01 - no commitment set")


def test_today_empty_not_today(mock_storage, mocker):
    mock_storage.get_day.return_value = ("2023-01-01", None)

    mock_print = mocker.patch("ot.commands.today_cmd.print")

    mock_datetime = mocker.patch("ot.commands.today_cmd.datetime")
    mock_datetime.now.return_value.strftime.return_value = "2023-01-02"

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 0
    mock_print.assert_called_with("2023-01-01 - no commitment set")


def test_today_generic_error(mock_storage):
    mock_storage.get_day.side_effect = Exception("Boom")

    result = runner.invoke(app, ["today"])

    assert result.exit_code == 1
    assert "Error retrieving data for None: Boom" in result.stdout
