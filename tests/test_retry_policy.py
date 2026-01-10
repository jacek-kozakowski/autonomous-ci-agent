import pytest
from unittest.mock import patch, MagicMock

from agent.retry import retry_policy


def test_retry_policy():

    assert retry_policy(0, []) is True
    assert retry_policy(1, ["AssertionError"]) is False
    assert retry_policy(3, ["ConnectionError"]) is False
    assert retry_policy(0, ["AssertionError", "ConnectionError"]) is False