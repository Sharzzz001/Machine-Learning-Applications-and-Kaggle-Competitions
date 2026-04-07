from pathlib import Path

# Root project name
PROJECT_NAME = "pmo-controls"

# Folder structure definition
STRUCTURE = {
    "data": ["raw", "processed"],
    "src": ["ingestion", "controls", "ai", "dashboard", "notifications"],
    "configs": [],
    "pipelines": [],
    "tests": []
}

# Files to create
FILES = [
    "requirements.txt",
    "README.md",
    "configs/jira_config.yaml",
    "configs/rag_rules.yaml",
    "configs/email_templates.yaml",
    "pipelines/run_pipeline.py"
]


def create_structure(base_path: Path):
    # Create root directory
    base_path.mkdir(exist_ok=True)

    # Create folders
    for parent, children in STRUCTURE.items():
        parent_path = base_path / parent
        parent_path.mkdir(exist_ok=True)

        for child in children:
            (parent_path / child).mkdir(exist_ok=True)

    # Create files
    for file in FILES:
        file_path = base_path / file
        file_path.parent.mkdir(parents=True, exist_ok=True)  # ensure parent exists
        file_path.touch(exist_ok=True)

    print(f"✅ Project structure created at: {base_path.resolve()}")


if __name__ == "__main__":
    project_path = Path(PROJECT_NAME)
    create_structure(project_path)