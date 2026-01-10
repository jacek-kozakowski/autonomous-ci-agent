import pytest
from logic.calc import add, sub

def test_add():
    assert add(2, 2) == 4

def test_sub():
    assert sub(2, 2) == 0