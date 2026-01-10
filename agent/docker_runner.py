import subprocess
from pathlib import Path
from typing import Any
def build_image(repo_path: str) -> dict[str, Any]:

    build_script = """
    set -e
    if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt.txt ]; then
        pip install -U pip 
        pip install -r requirements.txt.txt || pip install .
    fi 
    
    if [ -f CMakeLists.txt ] ; then
        cmake -S . -B build
        cmake --build build
    elif [ -f Makefile ] ; then
        make
    fi
    """

    cmd = [
        "docker", "run" , "--rm",
        "-v", f"{repo_path}:/workspace",
        "ci-image",
        "bash", "-c", build_script
    ]
    repo_path = Path(repo_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "python_detected" : repo_path.joinpath("pyproject.toml").exists() or
                            repo_path.joinpath("setup.py").exists() or
                            repo_path.joinpath("requirements.txt.txt").exists(),
        "cpp_detected" : repo_path.joinpath("CMakeLists.txt").exists() or repo_path.joinpath("Makefile").exists()
    }