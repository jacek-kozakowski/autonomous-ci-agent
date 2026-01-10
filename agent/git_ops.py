import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def clone_repo(repo_url: str) -> str:
    repos_dir = BASE_DIR / "repos"
    repos_dir.mkdir(exist_ok=True)
    repo_name = repo_url.split("/")[-1]
    counter = 1
    while True:
        target_dir = repos_dir / f"{repo_name}_{counter}"
        if not target_dir.exists():
            break
        counter += 1
    subprocess.run(["git", "clone", repo_url, str(target_dir)])
    return str(target_dir)