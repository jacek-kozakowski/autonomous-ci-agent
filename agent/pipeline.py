from typing import TypedDict, List, Dict, Any, Set
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .git_ops import clone_repo
from .docker_runner import build_image, run_tests
from .log_parser import parse_test_logs
from .retry import retry_policy, patch_retry_policy
from .fixer import propose_fix_parallel, apply_fix

load_dotenv()
llm = ChatOpenAI(model="gpt-5.1")

class AgentState(TypedDict):
    repo_url: str
    repo_path: str
    build_logs: Dict[str, Any]
    test_logs: str
    failing_tests: List[str]
    error_types: Set[str]
    suspected_files: Set[str]
    test_results: Dict[str, Any]
    proposed_fixes: Dict[str, str]
    patch: int
    retries: int

def _clone_repo_node(state: AgentState) -> AgentState:
    """
    Node that clones the repo from the repo_url
    """
    if state["repo_url"] is None or not state["repo_url"].endswith(".git"):
        return {
            **state,
        }

    repo_path = clone_repo(state["repo_url"])
    return {
        **state,
        "repo_path": repo_path
    }

def _build_node(state: AgentState) -> AgentState:
    """
    Node for compiling and building the repo
    """
    result = build_image(state["repo_path"])
    print(f"Built image with code {result.get('exit_code', 1)}")
    if result.get("exit_code", 1) != 0:
        print(result.get("stderr", "No build logs found."))
    return {
        **state,
        "build_logs": result
    }

def _run_tests_node(state: AgentState) -> AgentState:
    build_logs = state.get("build_logs", {})

    if not build_logs or build_logs.get("exit_code", 1) != 0:
        print("Build failed, skipping tests.")
        return state

    is_python = build_logs.get("python_detected", False)
    is_cpp = build_logs.get("cpp_detected", False)

    result = run_tests(state["repo_path"], is_python, is_cpp)

    retries = 0 if state.get("retries") is None else state["retries"] + 1
    return {
        **state,
        "test_logs": result["stdout"] + "\n" + result["stderr"],
        "retries": retries,
    }

def _analyze_test_logs_node(state: AgentState) -> AgentState:
    parsed_tests = parse_test_logs(state["repo_path"])

    test_results = {
        "stage": "tests",
        "status": "success" if not parsed_tests["errors"] else "failed",
        "attempt": state["retries"],
        "errors": parsed_tests["errors"],
    }
    print(f"Analyzed test logs. Status = {test_results['status']}, Errors = {len(test_results['errors'])}.")

    return {
        **state,
        "failing_tests": parsed_tests["failing_tests"],
        "error_types": parsed_tests["error_types"],
        "suspected_files": parsed_tests["suspected_files"],
        "test_results": test_results
    }


def _propose_fix_node(state: AgentState) -> AgentState:
    """
    Node for proposing or generating a fix using LLM
    """
    if not state["test_results"]["status"]:
        print("No failing tests found, skipping fix proposal.")
        return state

    fixes = propose_fix_parallel(llm, state["repo_path"], state["test_results"])
    print(f"Proposed {len(fixes)} fixes.")
    return {
        **state,
        "proposed_fixes": fixes,
        "patch" : state["patch"] + 1
    }


def _apply_patch_node(state: AgentState) -> AgentState:
    proposed_fixes = state["proposed_fixes"]
    if not proposed_fixes:
        print("No proposed fixes found, skipping patch application.")
        return state
    apply_fix(state["repo_path"], proposed_fixes, state["patch"])
    return state



def _check_retries(state: AgentState) -> str:
    if state["test_results"]["status"] == "success":
        print("All tests passed! Ending pipeline...")
        return "end"
    if retry_policy(state["retries"], state["error_types"]):
        return "retry"
    else:
        return "abort"


def _check_repo_cloned(state: AgentState) -> str:
    repo_path = state.get("repo_path", None)
    repo_url = state.get("repo_url", None)
    if repo_path:
        return "skip_clone"
    elif repo_url:
        return "do_clone"
    else:
        print("No repo URL or path provided, aborting.")
        return "abort"

def _check_patch_retries(state: AgentState) -> str:
    if patch_retry_policy(state["patch"]):
        print("Max patch attempts reached, aborting.")
        return "abort"
    else:
        return "retry"

def _check_build_failed(state: AgentState) -> str:
    build_logs = state.get("build_logs", {})
    return "abort" if build_logs.get("exit_code", 1) != 0 else "continue"

def create_graph():
    graph = StateGraph(state_schema=AgentState)
    graph.add_node("CloneRepoNode", _clone_repo_node)
    graph.add_node("BuildNode", _build_node)
    graph.add_node("RunTestsNode", _run_tests_node)
    graph.add_node("AnalyzeTestLogsNode", _analyze_test_logs_node)
    graph.add_node("ProposeFixNode", _propose_fix_node)
    graph.add_node("ApplyPatchNode", _apply_patch_node)
    graph.add_conditional_edges(
        START,
        _check_repo_cloned,
        {
            "skip_clone": "BuildNode",
            "do_clone": "CloneRepoNode",
            "abort": END
        }
    )
    graph.add_edge("CloneRepoNode", "BuildNode")
    graph.add_conditional_edges(
        "BuildNode",
        _check_build_failed,
        {
            "continue": "RunTestsNode",
            "abort": END
        }
    )
    graph.add_edge("RunTestsNode", "AnalyzeTestLogsNode")
    graph.add_conditional_edges(
        "AnalyzeTestLogsNode",
        _check_retries,
        {
            "retry": "RunTestsNode",
            "abort": "ProposeFixNode",
            "end" : END
        }
    )
    graph.add_edge("ProposeFixNode", "ApplyPatchNode")
    graph.add_conditional_edges(
        "ApplyPatchNode",
        _check_patch_retries,
        {
            "retry": "BuildNode",
            "abort": END
        }
    )

    return graph.compile()
