from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

from git_ops import clone_repo
from docker_runner import build_image
from retry import retry_policy

class AgentState(TypedDict):
    repo_url: str
    repo_path: str
    build_logs: Dict[str, Any]
    test_logs: str
    failing_tests: List[str]
    error_types: List[str]
    suspected_files: List[str]
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
    """
    Node for unit/integration running tests
    """
    return state

def analyze_logs_node(state: AgentState) -> AgentState:
    """
    Node for parsing build/test logs
    """
    return state

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
