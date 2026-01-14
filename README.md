# Autonomous CI Agent

An intelligent CI/CD agent that automatically detects, analyzes, and fixes failing tests in codebase using LLM-powered code generation.

## Overview

This project implements an autonomous CI/CD pipeline that:
- **Clones** repositories or works with local codebases
- **Builds** projects (Python & C++ support)
- **Runs tests** in isolated Docker containers
- **Analyzes** test failures using intelligent log parsing
- **Proposes fixes** using GPT-4 powered agents
- **Applies patches** automatically and retries tests

## ️ Architecture

The system is built using LangGraph for orchestrating the CI pipeline as a state machine.

### Key Components

- **`pipeline.py`**: LangGraph state machine orchestrating the entire CI flow
- **`docker_runner.py`**: Isolated build and test execution in Docker containers
- **`log_parser.py`**: Intelligent parsing of pytest/ctest output
- **`fixer.py`**: LLM-powered code analysis and fix generation
- **`git_ops.py`**: Repository cloning and management
- **`retry.py`**: Smart retry policies for flaky vs. deterministic failures

## Quick Start

### Prerequisites

- Python 3.10+
- Docker
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jacek-kozakowski/autonomous-ci-agent.git
   cd AIDevOps
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to .env
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

4. **Configure settings**
   ```json
   // Edit settings/settings.json to adjust retry policies 
   {
     "max_retries": 3,
     "max_patches": 2
   }
   ```

### Usage

Run the agent with a repository URL or local path:

```bash
python main.py
```

**Example session:**
```
Enter repo URL or path: https://github.com/user/project.git
# or
Enter repo URL or path: ./examples/calc_app
```

The agent will:
1. Clone/load the repository
2. Build the project
3. Run tests
4. If tests fail → analyze logs → propose fixes → apply patches → retry
5. Generate detailed change logs in `changes/CHANGES_*.md`


##  How It Works

### 1. Build Detection
Automatically detects project type:
- Python: Looks for `requirements.txt`, `setup.py`, `pyproject.toml`
- C++: Looks for `CMakeLists.txt`, `Makefile`

### 2. Test Execution
Runs tests in isolated Docker containers:
- Python: `pytest`
- C++: `ctest --output-on-failure`

### 3. Log Analysis
Parses test output to extract:
- Failing test names
- Error types (AssertionError, etc.)
- File paths and line numbers
- Error messages

### 4. Fix Generation
Uses GPT-4 agent with tools:
- `read_repo_file`: Reads source files
- Analyzes code structure and test failures
- Generates complete fixed file content

### 5. Patch Application
- Applies fixes to source files
- Generates diff-based change logs
- Rebuilds and retests

