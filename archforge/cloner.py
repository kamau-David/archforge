"""
cloner.py — clones a target GitHub repo into a local working directory
so it can be analyzed by the rest of ArchForge.
"""

import subprocess
import shutil
from pathlib import Path


def clone_repo(repo_url: str, workdir: str = "workspace") -> Path:
    """
    Clones repo_url into <workdir>/<repo_name>, replacing it if it already
    exists there. Returns the local path to the cloned repo.
    """
    workdir_path = Path(workdir)
    workdir_path.mkdir(exist_ok=True)

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target_path = workdir_path / repo_name

    if target_path.exists():
        print(f"[cloner] '{target_path}' already exists — removing for a fresh clone.")
        shutil.rmtree(target_path)

    print(f"[cloner] Cloning {repo_url} into {target_path} ...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(target_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"[cloner] git clone failed:\n{result.stderr}")

    print(f"[cloner] Done. Repo available at: {target_path}")
    return target_path


if __name__ == "__main__":
    # quick manual test
    path = clone_repo("https://github.com/mdanics/fluttergram.git")
    print(f"Cloned to: {path.resolve()}")