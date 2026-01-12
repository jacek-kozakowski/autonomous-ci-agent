from pathlib import Path

from langchain_core.tools import tool
from langchain.agents import create_agent
import re

def get_file_structure(repo_path: str) -> str:
    """"
    returns a string representation of the file structure of the repo
    """
    structure = []
    for root, dirs, files in Path(repo_path).walk():

        root_str = str(root)
        if ".git" in root_str or "__pycache__" in root_str or ".venv" in root_str:
            continue
        for file in files:
            if file.endswith((".py", ".cpp", ".h", ".c")):
                rel_path = root.relative_to(repo_path)
                structure.append(str(rel_path / file))

    return "\n".join(structure)


def parse_fix_response(response_text: str) -> dict[str, str]:
    """
    Parses the response from the agent into a dictionary of source file paths and their updated content.
    """
    fixes = {}
    parts = re.split(r'(?=SOURCE_FILE:)', response_text)
    for part in parts:
        if "SOURCE_FILE:" not in part:
            continue

        file_match = re.search(r"SOURCE_FILE:\s*(.*)", part)
        if not file_match:
            continue
        file_path = file_match.group(1)
        code_match = re.search(r"FIXED_CODE:\n```python\n(.*)\n```", part, re.DOTALL)
        if code_match:
            new_code = code_match.group(1)
            fixes[file_path] = new_code

    if not fixes:
        print("[Parse Warning] No fixes found in the response.")

    return fixes



def propose_fix(llm, repo_path: str, test_results: dict,
                failing_tests: list[str]) -> dict[str, str]:
    file_structure = get_file_structure(repo_path)

    @tool
    def read_repo_file(relative_path: str) -> str:
        """
        Reads a file from the repo.
        :param relative_path:
        :return: content of the file
        """
        full_path = Path(repo_path) / relative_path
        try:
            return full_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file {full_path}: {str(e)}"

    tools = [read_repo_file]
    agent_exec = create_agent(llm, tools=tools)
    prompt = f"""
    You are an expert dev ops developer debugging a CI pipeline. 
    
    REPO STRUCTURE:
    {file_structure}
    
    FAILING TESTS:
    {failing_tests}
    
    LOGS:
    {test_results}
    
    YOUR TASK:
    1. Analyze the LOGS and FAILING TESTS to deduce which SOURCE FILES (implementation) are broken using REPO STRUCTURE.
    2. Use the `read_repo_file` tool to read the contents of the suspected source code files (and tests if needed).
    3. Analyze the code to find the bug/problem and understand it in detail.
    4. If there is no bug in the SOURCE FILE, analyze the test and if there is a bug propose a fix of the test file. 
    4. Propose a fix by proposing the COMPLETE updated content of the fixed source file.
    
    Make sure you only change the code that is not passing the tests and do not fix any other code no matter how minor the change would be.
    
    OUTPUT FORMAT:
    It is crucial that you return the fix plan in the following format:
    SOURCE_FILE: <path>
    FIXED_CODE:
    ```python
    <complete updated source code>
    ```
    """

    response = agent_exec.invoke({"messages": [("user", prompt)]})

    last_message = response["messages"][-1].content
    
    return parse_fix_response(last_message)


def apply_fix(repo_path: str, fixes: dict[str, str]):
    if not fixes:
        print("No fixes to apply.")
        return

    for file_path, new_code in fixes.items():
        try:
            full_path = Path(repo_path) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(new_code, encoding='utf-8')
            print(f"Applied fix to {file_path}")
        except Exception as e:
            print(f"Failed to apply fix to {file_path}: {e}")

