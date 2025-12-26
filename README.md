# Transcription Bot Project


# Usage

This project utilizes Poetry for dependency management and virtual environment creation. Please install Poetry before running this project.

1.  **Install Dependencies:**
    ```bash
    poetry install
    ```
    This command will:
    *   Create a virtual environment for the project.
    *   Install all the dependencies listed in the `pyproject.toml` file.

2. **Execute the Script:**
    ```bash
    poetry run python src/main.py
    ```
    This ensures your script runs within the isolated Poetry-managed environment.

## Dependency Management

Poetry is used for managing dependencies.  It utilizes a `pyproject.toml` file to track and manage all project dependencies.  Changes to dependencies are handled using `poetry add <package>` or `poetry remove <package>`.
