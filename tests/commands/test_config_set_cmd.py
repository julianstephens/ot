import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import StorageNotInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_config_set_default_log_days(mock_storage, mocker):
    mock_prompt = mocker.patch("ot.commands.config_cmd.set_cmd.Prompt.ask")
    mock_prompt.return_value = "10"

    result = runner.invoke(app, ["config", "set", "default_log_days"])

    assert result.exit_code == 0
    assert "Configuration 'default_log_days' updated successfully." in result.stdout
    assert mock_storage.settings.default_log_days == 10
    mock_storage.modify_settings.assert_called_once()


def test_config_set_default_log_days_invalid(mock_storage, mocker):
    mock_prompt = mocker.patch("ot.commands.config_cmd.set_cmd.Prompt.ask")
    mock_prompt.return_value = "-1"

    result = runner.invoke(app, ["config", "set", "default_log_days"])

    assert result.exit_code == 1
    assert "Please enter a valid positive integer for days." in result.stdout


def test_config_set_prompt_on_empty(mock_storage, mocker):
    mock_confirm = mocker.patch("ot.commands.config_cmd.set_cmd.Confirm.ask")
    mock_confirm.return_value = False

    result = runner.invoke(app, ["config", "set", "auto_prompt_on_empty"])

    assert result.exit_code == 0
    assert "Configuration 'auto_prompt_on_empty' updated successfully." in result.stdout
    assert mock_storage.settings.auto_prompt_on_empty is False
    mock_storage.modify_settings.assert_called_once()


def test_config_set_strict_mode(mock_storage, mocker):
    mock_confirm = mocker.patch("ot.commands.config_cmd.set_cmd.Confirm.ask")
    mock_confirm.return_value = True

    result = runner.invoke(app, ["config", "set", "strict_mode"])

    assert result.exit_code == 0
    assert "Configuration 'strict_mode' updated successfully." in result.stdout
    assert mock_storage.settings.strict_mode is True
    mock_storage.modify_settings.assert_called_once()


def test_config_set_unknown_key(mock_storage):
    result = runner.invoke(app, ["config", "set", "unknown_key"])

    assert result.exit_code == 2  # Typer validation error for Enum


def test_config_set_not_initialized(mock_storage, mocker):
    mock_prompt = mocker.patch("ot.commands.config_cmd.set_cmd.Prompt.ask")
    mock_prompt.return_value = "10"
    mock_storage.modify_settings.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["config", "set", "default_log_days"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_config_set_generic_error(mock_storage, mocker):
    mock_prompt = mocker.patch("ot.commands.config_cmd.set_cmd.Prompt.ask")
    mock_prompt.return_value = "10"
    mock_storage.modify_settings.side_effect = Exception("Boom")

    result = runner.invoke(app, ["config", "set", "default_log_days"])

    assert result.exit_code == 1
    assert "Error setting default_log_days: Boom" in result.stdout
