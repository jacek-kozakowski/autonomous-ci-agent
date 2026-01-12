from agent.pipeline import create_graph
from pathlib import Path

state = {
    "retries": 0,
    "patch": 0,
}

if __name__ == "__main__":
    graph = create_graph()

    print("\033[92mAutonomous CI Agent started.")
    repo = input("Enter repo URL or path: ")

    if repo.endswith(".git"):
        state["repo_url"] = repo
        graph.invoke(state)
    else:
        path = Path(repo)
        if path.exists() and path.is_dir():
            state["repo_path"] = repo
            graph.invoke(state)
        else:
            print("Invalid repo path or URL.")
    print("\033[00m")