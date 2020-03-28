# import copy
# import json
# import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Text

from . import constants
from .utils import ensure_repo

# import jinja2
# import jsonschema
# import pandas
# import pyemojify
# import pytest
# import yaml


@dataclass
class Generator:
    workdir: Path
    lsp_dir: Optional[Path] = None
    vlspn_dir: Optional[Path] = None

    lsp_repo = constants.LSP_REPO
    lsp_committish = constants.LSP_COMMIT
    lsp_spec_version = constants.LSP_SPEC_VERSION

    vlspn_repo = constants.VLSPN_REPO
    vlspn_committish = constants.VLSPN_COMMIT

    raw_spec: Optional[Text] = None

    def generate(self) -> int:
        self.ensure_repos()
        self.parse_spec()
        return 0

    def ensure_repos(self):
        if not self.workdir.exists():
            self.workdir.mkdir(parents=True)

        self.lsp_dir = ensure_repo(self.workdir, self.lsp_repo, self.lsp_committish)
        self.vlspn_dir = ensure_repo(
            self.workdir, self.vlspn_repo, self.vlspn_committish
        )

    def parse_spec(self):
        if self.lsp_dir is None:
            raise ValueError
        spec_md = (
            self.lsp_dir
            / "_specifications"
            / f"""specification-{self.lsp_spec_version.replace('.', '-')}.md"""
        )
        self.raw_spec = spec_md.read_text()