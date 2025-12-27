import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import DayUnsetError, StorageNotInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_note_success(mock_storage):
    result = runner.invoke(app, ["note", "test note"])

    assert result.exit_code == 0
    assert "Note added: test note" in result.stdout
    mock_storage.add_note.assert_called_once_with(message="test note", date=None)


def test_note_with_date(mock_storage):
    result = runner.invoke(app, ["note", "test note", "--date", "2023-01-01"])

    assert result.exit_code == 0
    mock_storage.add_note.assert_called_once_with(
        message="test note", date="2023-01-01"
    )


def test_note_not_initialized(mock_storage):
    mock_storage.add_note.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["note", "test note"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_note_day_unset_no_prompt(mock_storage):
    mock_storage.add_note.side_effect = DayUnsetError
    mock_storage.settings.auto_prompt_on_empty = False

    result = runner.invoke(app, ["note", "test note"])

    assert result.exit_code == 1
    assert "Cannot add note to day without a commitment set" in result.stdout


def test_note_day_unset_prompt_success(mock_storage, mocker):
    # First call raises DayUnsetError, second call succeeds
    mock_storage.add_note.side_effect = [DayUnsetError, None]
    mock_storage.settings.auto_prompt_on_empty = True
    mock_prompt = mocker.patch("ot.commands.note_cmd.prompt_set_commitment")

    result = runner.invoke(app, ["note", "test note"])

    assert result.exit_code == 0
    assert "Note added: test note" in result.stdout
    mock_prompt.assert_called_once_with(mock_storage)
    assert mock_storage.add_note.call_count == 2


def test_note_day_unset_prompt_fail(mock_storage, mocker):
    # First call raises DayUnsetError, second call raises Exception
    mock_storage.add_note.side_effect = [DayUnsetError, Exception("Boom")]
    mock_storage.settings.auto_prompt_on_empty = True
    mocker.patch("ot.commands.note_cmd.prompt_set_commitment")

    result = runner.invoke(app, ["note", "test note"])

    assert result.exit_code == 1
    assert "Error adding note after setting commitment: Boom" in result.stdout


def test_note_generic_error(mock_storage):
    mock_storage.add_note.side_effect = Exception("Boom")

    result = runner.invoke(app, ["note", "test note"])

    assert result.exit_code == 1
    assert "Error adding note: Boom" in result.stdout
