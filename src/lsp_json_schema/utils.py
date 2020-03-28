import json
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


def ensure_js_package(root: Path, package: Text, version: Text) -> None:
    package_json = json.loads((root / "package.json").read_text())
    in_json = package_json["devDependencies"].get(package)
    if in_json is None or version not in in_json:
        subprocess.check_call(
            ["npm", "install", "--save-dev", f"{package}@{version}"], cwd=root
        )
        subprocess.check_call(["npm", "install"], cwd=root)
