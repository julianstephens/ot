import pytest
from typer.testing import CliRunner

from ot.cli import app
from ot.utils import DayCollisionError, StorageNotInitializedError

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_set_success(mock_storage):
    result = runner.invoke(app, ["set", "My Commitment"])

    assert result.exit_code == 0
    assert "Commitment set for today: My Commitment" in result.stdout
    mock_storage.add_day.assert_called_once()
    _, kwargs = mock_storage.add_day.call_args
    assert kwargs["data"].title == "My Commitment"
    assert kwargs["date"] is None
    assert kwargs["force"] is False


def test_set_with_date(mock_storage):
    result = runner.invoke(app, ["set", "My Commitment", "--date", "2023-01-01"])

    assert result.exit_code == 0
    assert "Commitment set for 2023-01-01: My Commitment" in result.stdout
    _, kwargs = mock_storage.add_day.call_args
    assert kwargs["date"] == "2023-01-01"


def test_set_empty_title(mock_storage):
    result = runner.invoke(app, ["set", "   "])

    assert result.exit_code == 1
    assert "Title cannot be empty" in result.stdout


def test_set_not_initialized(mock_storage):
    mock_storage.add_day.side_effect = StorageNotInitializedError

    result = runner.invoke(app, ["set", "My Commitment"])

    assert result.exit_code == 1
    assert "Storage is not initialized" in result.stdout


def test_set_collision_no_force(mock_storage):
    mock_storage.add_day.side_effect = DayCollisionError

    result = runner.invoke(app, ["set", "My Commitment"])

    assert result.exit_code == 1
    assert (
        "A commitment is already set for this date. Use --force to overwrite."
        in result.stdout
    )


def test_set_collision_force(mock_storage):
    # If force is True, add_day shouldn't raise DayCollisionError
    # (handled in storage service)
    # But if it did (e.g. mock behavior), the command handles it.
    # However, the command passes force=True to add_day.

    result = runner.invoke(app, ["set", "My Commitment", "--force"])

    assert result.exit_code == 0
    _, kwargs = mock_storage.add_day.call_args
    assert kwargs["force"] is True


def test_set_generic_error(mock_storage):
    mock_storage.add_day.side_effect = Exception("Boom")

    result = runner.invoke(app, ["set", "My Commitment"])

    assert result.exit_code == 1
    assert "Error setting commitment: Boom" in result.stdout
