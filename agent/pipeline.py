from typing import TypedDict, List, Dict, Any, Set
from langgraph.graph import StateGraph, START, END

from git_ops import clone_repo
from docker_runner import build_image, run_tests
from log_parser import parse_test_logs
from retry import retry_policy

class AgentState(TypedDict):
    repo_url: str
    repo_path: str
    build_logs: Dict[str, Any]
    test_logs: str
    failing_tests: List[str]
    error_types: Set[str]
    suspected_files: Set[str]
    test_results: Dict[str, Any]
    patch: int
    retries: int

def clone_repo_node(state: AgentState) -> AgentState:
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

def build_node(state: AgentState) -> AgentState:
    """
    Node for compiling and building the repo
    """
    result = build_image(state["repo_path"])
    return {
        **state,
        "build_logs": Dict(result)
    }

def run_tests_node(state: AgentState) -> AgentState:
    build_logs = state.get("build_logs", {})

    is_python = build_logs.get("python_detected", False)
    is_cpp = build_logs.get("cpp_detected", False)

    result = run_tests(state["repo_path"], is_python, is_cpp)

    retries = 0 if state.get("retries") is None else state["retries"] + 1
    return {
        **state,
        "test_logs": result["stdout"] + "\n" + result["stderr"],
        "retries": retries,
    }

def analyze_logs_node(state: AgentState) -> AgentState:
    parsed_tests = parse_test_logs(state["test_logs"])
    test_results = {
        "stage" : "tests",
        "status" : "success" if not parsed_tests["failing_tests"] else "failed",
        "attempt" : state["retries"],
        "errors" : parsed_tests["errors"],
    }
    return {
        **state,
        "failing_tests": parsed_tests["failing_tests"],
        "error_types": parsed_tests["error_types"],
        "suspected_files": parsed_tests["suspected_files"],
        "test_results": test_results
    }

def propose_fix_node(state: AgentState) -> AgentState:
    """
    Node for proposing or generating a fix using LLM
    """
    return state

def apply_patch_node(state: AgentState) -> AgentState:
    """
    Node for applying the patch
    """
    return state

def deploy_node(state: AgentState) -> AgentState:
    """
    Node for deploying the patch to the sandbox
    """
    return state


def check_retries(state: AgentState) -> str:
    if retry_policy(state["retries"], state["error_types"]):
        return "retry"
    else:
        return "abort"


def check_repo_cloned(state: AgentState) -> str:
    repo_path = state["repo_path"]
    repo_url = state["repo_url"]
    if repo_path:
        return "skip_clone"
    elif repo_url:
        return "do_clone"
    else:
        return "abort"


graph = StateGraph()
graph.add_node("CloneRepoNode", clone_repo_node)
graph.add_node("BuildNode", build_node)
graph.add_node("RunTestsNode", run_tests_node)
graph.add_node("AnalyzeLogsNode", analyze_logs_node)
graph.add_node("ProposeFixNode", propose_fix_node)
graph.add_node("ApplyPatchNode", apply_patch_node)
graph.add_node("DeployNode", deploy_node)
graph.add_conditional_edges(
    START,
    check_repo_cloned,
    {
        "skip_clone": "BuildNode",
        "do_clone": "CloneRepoNode",
        "abort": END
    }
)
graph.add_edge("CloneRepoNode", "BuildNode")
graph.add_edge("BuildNode", "RunTestsNode")
graph.add_edge("RunTestsNode", "AnalyzeLogsNode")
graph.add_conditional_edges(
    "AnalyzeLogsNode",
    check_retries,
    {
        "retry": "RunTestsNode",
        "abort": "ProposeFixNode"
    }
)
graph.add_edge("ProposeFixNode", "ApplyPatchNode")
graph.add_edge("ApplyPatchNode", "DeployNode")
graph.add_edge("DeployNode", END)
