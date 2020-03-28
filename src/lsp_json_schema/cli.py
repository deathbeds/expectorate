import sys
from pathlib import Path
from typing import Text

import click

from . import constants
from ._version import __version__
from .api import Generator


@click.command()
@click.version_option(__version__)
@click.option("--workdir", "-w", default=Path.cwd() / "work", type=Path)
@click.option("--output", "-o", default=Path.cwd() / "output", type=Path)
@click.option("--lsp-spec-version", default=constants.LSP_SPEC_VERSION)
@click.option("--lsp-repo", default=constants.LSP_REPO)
@click.option("--lsp-committish", default=constants.LSP_COMMIT)
@click.option("--vlspn-repo", default=constants.VLSPN_REPO)
@click.option("--vlspn-committish", default=constants.VLSPN_COMMIT)
def cli(
    workdir: Path,
    output: Path,
    lsp_spec_version: Text,
    lsp_repo: Text,
    lsp_committish: Text,
    vlspn_repo: Text,
    vlspn_committish: Text,
):
    """ lsp-json-schema
    """
    gen = Generator(
        workdir=workdir,
        output=output,
        lsp_spec_version=lsp_spec_version,
        lsp_repo=lsp_repo,
        lsp_committish=lsp_committish,
        vlspn_repo=vlspn_repo,
        vlspn_committish=vlspn_committish,
    )
    sys.exit(gen.generate())
