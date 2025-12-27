import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import StorageAlreadyInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_init_success(mock_storage):
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Storage initialized successfully." in result.stdout
    mock_storage.initialize.assert_called_once_with(force=False)


def test_init_force(mock_storage):
    result = runner.invoke(app, ["init", "--force"])

    assert result.exit_code == 0
    assert "Force option enabled" in result.stdout
    assert "Storage initialized successfully." in result.stdout
    mock_storage.initialize.assert_called_once_with(force=True)


def test_init_already_initialized(mock_storage):
    mock_storage.initialize.side_effect = StorageAlreadyInitializedError

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "Storage is already initialized. Use --force to overwrite." in result.stdout


def test_init_generic_error(mock_storage):
    mock_storage.initialize.side_effect = Exception("Boom")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "Failed to initialize storage." in result.stdout
