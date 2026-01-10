import pytest
from unittest.mock import patch, MagicMock
from agent.docker_runner import *

@patch("subprocess.run")
@patch("pathlib.Path.joinpath")
def test_build_image(mock_joinpath, mock_run):

    def join_path_side_effect(name):
        mock_path = MagicMock()
        mock_path.exists.return_value = (name == "pyproject.toml")
        return mock_path
    mock_joinpath.side_effect = join_path_side_effect

    mock_run.return_value = MagicMock(returncode=0,
                                      stdout="Build success",
                                      stderr="")

    result = build_image("tests/test_repo")

    args, _ = mock_run.call_args
    command_list = args[0]

    assert "docker" in command_list
    assert "tests/test_repo:/workspace" in command_list

    assert result["python_detected"] is True
    assert result["cpp_detected"] is False
    assert result["exit_code"] == 0

@patch("subprocess.run")
def test_run_tests_python(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Test success", stderr="")

    result = run_tests("tests/test_repo", True, False)

    args, _ = mock_run.call_args
    command_list = args[0]
    test_script = command_list[-1]
    assert "docker" in command_list
    assert "tests/test_repo:/workspace" in command_list
    assert "pip install pytest" in test_script
    assert "pytest" in test_script
    assert result["exit_code"] == 0

@patch("subprocess.run")
def test_run_tests_cpp(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Test success", stderr="")

    result = run_tests("tests/test_repo", False, True)

    args, _ = mock_run.call_args
    command_list = args[0]
    test_script = command_list[-1]
    assert "docker" in command_list
    assert "tests/test_repo:/workspace" in command_list
    assert "ctest --output-on-failure" in test_script
    assert "pytest" not in test_script
    assert result["exit_code"] == 0