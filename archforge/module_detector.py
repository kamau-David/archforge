"""
module_detector.py — scans a cloned repo and groups files into logical
"modules" based on folder structure, so ArchForge can analyze each
module independently.
"""

from pathlib import Path

IGNORE_DIRS = {
    ".git", ".idea", ".vscode", "build", "node_modules",
    "venv", "__pycache__", ".dart_tool", "ios", "android",
    ".gradle", "Pods", "assets",
}

# Folders whose *subfolders* should be split into separate modules
# (i.e. this folder is a container, not a module itself)
CONTAINER_DIRS = {"lib", "src", "app", "source"}

CODE_EXTENSIONS = {
    ".dart", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".kt", ".go", ".rb", ".swift", ".c", ".cpp", ".h",
}


def _is_code_file(path: Path) -> bool:
    return path.suffix in CODE_EXTENSIONS


def _code_files_in(folder: Path, repo_path: Path) -> list:
    return [
        str(f.relative_to(repo_path))
        for f in sorted(folder.rglob("*"))
        if f.is_file() and _is_code_file(f)
        and not any(ig in f.parts for ig in IGNORE_DIRS)
    ]


def detect_modules(repo_path: Path, min_files: int = 1) -> dict:
    """
    Scans every top-level folder in the repo (skipping ignored ones).
    - If a top-level folder is a known "container" (lib, src, app...),
      its immediate subfolders each become their own module, and any
      code files directly inside it become a "<name> (top-level)" module.
    - Any other top-level folder with code files becomes its own module
      directly (e.g. "functions").
    """
    repo_path = Path(repo_path)
    modules = {}

    for item in sorted(repo_path.iterdir()):
        if not item.is_dir() or item.name in IGNORE_DIRS or item.name.startswith("."):
            continue

        if item.name in CONTAINER_DIRS:
            # files directly inside the container (e.g. lib/main.dart)
            top_files = [
                f for f in item.iterdir()
                if f.is_file() and _is_code_file(f)
            ]
            if top_files:
                modules[f"{item.name} (top-level)"] = [
                    str(f.relative_to(repo_path)) for f in top_files
                ]

            # each subfolder becomes its own module
            for sub in sorted(item.iterdir()):
                if sub.is_dir() and sub.name not in IGNORE_DIRS:
                    files = _code_files_in(sub, repo_path)
                    if len(files) >= min_files:
                        modules[f"{item.name}/{sub.name}"] = files
        else:
            # treat this whole top-level folder as one module
            files = _code_files_in(item, repo_path)
            if len(files) >= min_files:
                modules[item.name] = files

    return modules


if __name__ == "__main__":
    repo = Path("workspace/fluttergram")
    result = detect_modules(repo)

    print(f"Detected {len(result)} module(s):\n")
    for module_name, files in result.items():
        print(f"[{module_name}] — {len(files)} file(s)")
        for f in files[:5]:
            print(f"    {f}")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")
        print()