from agent.log_parser import parse_test_logs

def test_parse_simple_failure():
    log_output = """
=================================== FAILURES ===================================
_________________________________ test_example _________________________________
    def test_example():
>       assert 1 == 2
E       AssertionError: assert 1 == 2

tests/test_simple.py:4: AssertionError
FAILED tests/test_simple.py::test_example
=========================== 1 failed in 0.05s ============================
    """
    
    result = parse_test_logs(log_output)
    
    assert "tests/test_simple.py::test_example" in result["failing_tests"]
    assert "AssertionError" in result["error_types"]
    assert "tests/test_simple.py" in result["suspected_files"]

def test_parse_multiple_failures():
    log_output = """
FAILED tests/api/test_login.py::test_login_failure
E   ValueError: Invalid token
FAILED tests/ui/test_dashboard.py::test_layout
E   RuntimeError: Timeout
    """
    
    result = parse_test_logs(log_output)
    
    assert len(result["failing_tests"]) == 2
    assert "tests/api/test_login.py::test_login_failure" in result["failing_tests"]
    assert "tests/ui/test_dashboard.py::test_layout" in result["failing_tests"]
    assert "ValueError" in result["error_types"]
    assert "RuntimeError" in result["error_types"]
    assert len(result["suspected_files"]) == 2

def test_parse_success():
    log_output = """
tests/test_good.py ..                                                    [100%]
============================== 2 passed in 0.01s ===============================
    """
    result = parse_test_logs(log_output)
    
    assert len(result["failing_tests"]) == 0
    assert len(result["error_types"]) == 0

def test_parse_real_output():
    log_output = """
========================================================================================================= test session starts ==========================================================================================================
platform darwin -- Python 3.12.0, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/jacek/AIDevOps
plugins: anyio-4.12.0, langsmith-0.6.0
collected 2 items                                                                                                                                                                                                                      

examples/calc_app/tests/test_calc.py F.                                                                                                                                                                                          [100%]

=============================================================================================================== FAILURES ===============================================================================================================
_______________________________________________________________________________________________________________ test_add _______________________________________________________________________________________________________________

    def test_add():
>       assert add(2, 2) == 4
E       assert 3 == 4
E        +  where 3 = add(2, 2)

examples/calc_app/tests/test_calc.py:5: AssertionError
======================================================================================================= short test summary info ========================================================================================================
FAILED examples/calc_app/tests/test_calc.py::test_add - assert 3 == 4
===================================================================================================== 1 failed, 1 passed in 0.04s ======================================================================================================
"""
    result = parse_test_logs(log_output)

    assert "examples/calc_app/tests/test_calc.py::test_add" in result["failing_tests"]
    assert "examples/calc_app/tests/test_calc.py" in result["suspected_files"]
    assert "AssertionError" in result["error_types"]

    assert len(result["errors"]) > 0
    error_entry = next((e for e in result["errors"] if e["type"] == "AssertionError" and e["file"] == "examples/calc_app/tests/test_calc.py"), None)
    assert error_entry is not None
    assert error_entry["line"] == 5
