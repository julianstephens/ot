import pytest
from typer.testing import CliRunner

from ot.cli import app

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service

    # Setup settings
    mock_service.settings.default_log_days = 7
    mock_service.settings.auto_prompt_on_empty = True
    mock_service.settings.strict_mode = False

    return mock_service


def test_config_view_success(mock_storage):
    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert "Current Configuration Settings:" in result.stdout
    assert "Default Log Days      : 7" in result.stdout
    assert "Auto Prompt on Empty  : True" in result.stdout
    assert "Strict Mode           : False" in result.stdout


def test_config_view_error(mock_storage, mocker):
    # We need to re-setup mock_storage or just use the one passed
    # But we need to patch the property.
    # mock_storage.settings is a Mock object by default (or configured in fixture).
    # To make accessing .settings raise, we can use PropertyMock.

    p = mocker.PropertyMock(side_effect=Exception("Boom"))
    type(mock_storage).settings = p

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 1
    assert "Error retrieving settings: Boom" in result.stdout
