import pytest
from unittest.mock import patch, MagicMock

from agent.git_ops import *


@patch("subprocess.run")
@patch("pathlib.Path.mkdir")
def test_clone_repo(mock_mkdir, mock_run, tmp_path):
    repo_url = "https://github.com/jacek-kozakowski/GraphEngine.git"

    result_path = clone_repo(repo_url)

    args, _ = mock_run.call_args
    command_list = args[0]
    assert "git" in command_list
    assert "clone" in command_list
    assert repo_url in command_list
    assert result_path.endswith("GraphEngine_1") is True

