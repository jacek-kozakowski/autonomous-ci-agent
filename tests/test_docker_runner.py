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