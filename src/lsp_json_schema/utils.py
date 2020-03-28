import subprocess
from pathlib import Path
from typing import Text
from urllib.parse import urlparse


def ensure_repo(workdir: Path, repo_url: Text, committish: Text) -> Path:
    repo_dir = workdir / Path(urlparse(repo_url).path).stem

    if not repo_dir.is_dir():
        subprocess.check_call(["git", "clone", repo_url, repo_dir])

    subprocess.check_call(["git", "checkout", "-f", committish], cwd=repo_dir)

    return repo_dir


def add_npm_packages(root: Path, *specs: Text) -> None:
    subprocess.check_call(["npm", "install", "--save", "--only=dev", *specs], cwd=root)
    subprocess.check_call(["npm", "install"], cwd=root)
