import xml.etree.ElementTree as ET
import re
from typing import Any
from pathlib import Path

def parse_test_logs(repo_path: str) -> dict[str, Any]:
    # Standard location for the report
    report_path = Path(repo_path) / "report.xml"
    
    if not report_path.exists():
        print(f"Warning: Test report not found at {report_path}")
        return {
            "failing_tests": [],
            "error_types": set(),
            "suspected_files": set(),
            "errors": []
        }

    tree = ET.parse(report_path)
    root = tree.getroot()

    errors = []
    failing_tests = []
    error_types = set()
    suspected_files = set()

    for testcase in root.iter('testcase'):
        issue = testcase.find('failure')
        if issue is None:
            issue = testcase.find('error')

        if issue is not None:
            test_name = testcase.get('name')
            classname = testcase.get('classname', '')
            failing_tests.append(f"{classname}::{test_name}")
            
            error_message = issue.text or issue.get('message', "unknown error")
            error_type = issue.get('type', "Failure")

            file_path = testcase.get('file') or issue.get('file')
            line_num_str = testcase.get('line') or issue.get('line')
            
            if not file_path:
                match = re.search(r"([\w/.-]+\.\w+):(\d+):", error_message)
                if match:
                    file_path = match.group(1)
                    line_num = int(match.group(2))
                else:
                    file_path = "unknown_file"
                    line_num = 0
            else:
                line_num = int(line_num_str) if line_num_str else 0

            errors.append({
                "type": error_type,
                "message": error_message.strip(),
                "file": file_path,
                "line": line_num
            })
            error_types.add(error_type)
            suspected_files.add(file_path)

    return {
        "failing_tests": failing_tests,
        "error_types": error_types,
        "suspected_files": suspected_files,
        "errors": errors
    }
