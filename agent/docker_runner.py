import subprocess
from pathlib import Path
from typing import Any

def ensure_ci_image_exists():
    check = subprocess.run(["docker", "build", "-t", "ci-image", "."], capture_output=True)

    if check.returncode == 0:
        print("CI image built successfully.")
        return

    project_root = Path(__file__).parent.parent
    docker_dir = project_root / "docker"

    if not docker_dir.exists():
        raise Exception(f"Docker directory not found at {docker_dir}.")

    result = subprocess.run(["docker", "build", "-t", "ci-image", "."], cwd=docker_dir, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Failed to build CI image: {result.stderr}")


def build_image(repo_path: str) -> dict[str, Any]:
    ensure_ci_image_exists()
    build_script = """
    set -e
    if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt ]; then
        pip install -U pip 
        pip install -r requirements.txt || pip install .
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
                            repo_path.joinpath("requirements.txt").exists(),
        "cpp_detected" : repo_path.joinpath("CMakeLists.txt").exists() or repo_path.joinpath("Makefile").exists()
    }

def run_tests(repo_path: str, is_python: bool, is_cpp: bool) -> dict[str, Any]:
    if is_python:
        test_script = """
        set -e
        if [ -f requirements.txt ]; then 
            pip install -r requirements.txt;
        fi
        pip install pytest async-timeout
        pytest
        """
    elif is_cpp:
        test_script = """
        set -e 
        if [ -d build ]; then 
            cd build;
            ctest --output-on-failure;
        else
            echo "No build directory found";
            exit 1;
        fi
        """
    cmd = ["docker", "run", "--rm",
           "-v", f"{repo_path}:/workspace",
           "ci-image", "bash", "-c", test_script]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }