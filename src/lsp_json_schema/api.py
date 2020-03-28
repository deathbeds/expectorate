# import copy
# import json
# import jinja2
# import jsonschema
# import pytest
# import yaml

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Text

import pandas
import pyemojify

from . import constants
from .utils import ensure_js_package, ensure_repo


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
    df: Optional[pandas.DataFrame] = None

    def generate(self) -> int:
        self.ensure_repos()
        self.parse_spec()
        self.ensure_js_deps()
        self.build_naive_schema()
        self.extract_spec_features()
        self.df_part_one()
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
            self.spec_features = (
                self.raw_spec.split("#### $ Notifications and Requests")[1]
                .split("### Implementation considerations")[0]
                .split("#### <a href")[1:]
            )

    def df_part_one(self):
        if self.spec_features:
            df = pandas.DataFrame(self.spec_features, columns=["_md"])
            md = df["_md"]
            df["method"] = md.apply(
                lambda md: re.findall(r"""\* method: '(.*)'""", md)[0]
            )
            df["_raw_params"] = md.apply(
                lambda md: re.findall(r"""\* params: (.*)""", md)[0]
            )
            df["title"] = md.apply(
                lambda md: md.split(">")[1].split("<")[0].strip().split("(")[0].strip()
            )
            df["type"] = md.apply(
                lambda md: pyemojify.emojify(
                    md.split(">")[1].split("<")[0].strip().split("(")[1]
                )
                .replace(")", "")
                .strip()
            )
            df["_raw_result"] = md.apply(
                lambda md: (
                    re.findall(r"""\* result: (.*)""", md, flags=re.M | re.I) or [None]
                )[0]
            )
            df["_raw_error"] = md.apply(
                lambda md: (
                    re.findall(r"""\* error: (.*)""", md, flags=re.M | re.I) or [None]
                )[0]
            )
            self.df = df.sort_values(["type", "method"]).set_index(["type", "method"])
