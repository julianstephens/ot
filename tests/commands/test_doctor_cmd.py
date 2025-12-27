import pytest
from typer.testing import CliRunner

from ot.cli import app

runner = CliRunner()


@pytest.fixture
def mock_storage(mocker):
    mock_get_storage = mocker.patch("ot.cli.get_storage")
    mock_service = mocker.MagicMock()
    mock_get_storage.return_value = mock_service
    return mock_service


def test_doctor_success(mock_storage):
    mock_storage.doctor.return_value = (None, "State file checked. No issues found.", 0)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "State file checked. No issues found." in result.stdout
    mock_storage.doctor.assert_called_once()


def test_doctor_issues_found(mock_storage):
    mock_storage.doctor.return_value = (None, "Issues found.", 1)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "Issues found." in result.stdout
    mock_storage.doctor.assert_called_once()
