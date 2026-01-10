from typing import Any
import re
def parse_test_logs(test_logs: str) -> dict[str, Any]:

    errors = []
    failing_tests = []
    error_types = set()
    suspected_files = set()

    failed_test_regex = re.compile(r"FAILED\s+(.*?)::(\w+)")
    error_regex = re.compile(r"E\s+(\w+Error):\s+(.*)")

    current_file = None
    lines = test_logs.split("\n")

    direct_error_regex = re.compile(r"(.*?):(\d+):\s+(\w+Error)")

    pending_errors = []

    for line in lines:
        match_fail = failed_test_regex.search(line)
        if match_fail:
            current_file = match_fail.group(1)
            test_name = match_fail.group(2)
            failing_tests.append(f"{current_file}::{test_name}")
            suspected_files.add(current_file)
            pending_errors = []
            continue
        
        match_error = error_regex.search(line)
        if match_error:
            error_type = match_error.group(1)
            message = match_error.group(2)
            
            pending_errors.append({
                "type": error_type,
                "message": message
            })
            error_types.add(error_type)
            continue

        match_direct = direct_error_regex.search(line)
        if match_direct:
            file_path = match_direct.group(1)
            line_num = int(match_direct.group(2))
            error_type = match_direct.group(3)
            
            error_types.add(error_type)
            suspected_files.add(file_path)

            found_msg = "See logs for details"
            
            for i in range(len(pending_errors) - 1, -1, -1):
                if pending_errors[i]["type"] == error_type:
                    found_msg = pending_errors[i]["message"]
                    pending_errors.pop(i)
                    break
            
            errors.append({
                "type": error_type,
                "message": found_msg, 
                "file": file_path,
                "line": line_num,
            })

    return {
        "failing_tests": failing_tests,
        "error_types": error_types,
        "suspected_files": suspected_files,
        "errors": errors
    }