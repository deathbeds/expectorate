# import copy
# import json
# import re
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Text

from . import constants
from .utils import ensure_js_package, ensure_repo

# import jinja2
# import jsonschema
# import pandas
# import pyemojify
# import pytest
# import yaml


@dataclass
class Generator:
    workdir: Path
    output: Path

    lsp_dir: Optional[Path] = None
    vlspn_dir: Optional[Path] = None

    lsp_repo = constants.LSP_REPO
    lsp_committish = constants.LSP_COMMIT
    lsp_spec_version = constants.LSP_SPEC_VERSION

    vlspn_repo = constants.VLSPN_REPO
    vlspn_committish = constants.VLSPN_COMMIT

    prettier_version = constants.PRETTIER_VERSION
    tssg_version = constants.TSSG_VERSION

    raw_spec: Optional[Text] = None
    naive_schema: Optional[Dict[Text, Any]] = None
    spec_features: Optional[List[Text]] = None

    def generate(self) -> int:
        self.ensure_repos()
        self.parse_spec()
        self.ensure_js_deps()
        self.build_naive_schema()
        self.extract_spec_features()
        return 0

    def ensure_repos(self):
        if not self.workdir.exists():
            self.workdir.mkdir(parents=True)

        self.lsp_dir = ensure_repo(self.workdir, self.lsp_repo, self.lsp_committish)
        self.vlspn_dir = ensure_repo(
            self.workdir, self.vlspn_repo, self.vlspn_committish
        )

    def parse_spec(self):
        if self.lsp_dir is not None:
            spec_md = (
                self.lsp_dir
                / "_specifications"
                / f"""specification-{self.lsp_spec_version.replace('.', '-')}.md"""
            )
            self.raw_spec = spec_md.read_text()

    def ensure_js_deps(self):
        if self.vlspn_dir is not None:
            ensure_js_package(self.vlspn_dir, constants.TSSG, self.tssg_version)
            ensure_js_package(self.vlspn_dir, "prettier", self.prettier_version)

    def build_naive_schema(self):
        proto = self.vlspn_dir / "protocol"
        self.naive_schema = json.loads(
            subprocess.check_output(
                [
                    "node",
                    self.vlspn_dir / "node_modules" / ".bin" / constants.TSSG,
                    "--path",
                    proto / "src" / "protocol.ts",
                    "--expose",
                    "all",
                ],
                cwd=proto,
            ).decode("utf-8")
        )

    def extract_spec_features(self):
        if self.raw_spec:
            self.md_features = (
                self.raw_spec.split("#### $ Notifications and Requests")[1]
                .split("### Implementation considerations")[0]
                .split("#### <a href")[1:]
            )
