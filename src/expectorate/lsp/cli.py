import sys
from typing import Text

import click

from ..context import Context
from . import constants
from .conventions import CONVENTIONS
from .generate import SpecGenerator


@click.command()
@click.pass_context
@click.option("--lsp-spec-version", default=constants.LSP_SPEC_VERSION)
@click.option("--lsp-repo", default=constants.LSP_REPO)
@click.option("--lsp-committish", default=constants.LSP_COMMIT)
@click.option("--vlspn-repo", default=constants.VLSPN_REPO)
@click.option("--vlspn-committish", default=constants.VLSPN_COMMIT)
def lsp(
    ctx: Context,
    lsp_spec_version: Text,
    lsp_repo: Text,
    lsp_committish: Text,
    vlspn_repo: Text,
    vlspn_committish: Text,
):
    """ generate a JSON schema from:
        - Language Server Protocol (lsp) specification
        - vscode-languageserver-node reference implementation
    """

    lsp_spec = (
        CONVENTIONS.get(lsp_spec_version) or CONVENTIONS[constants.LSP_SPEC_VERSION]
    )

    assert lsp_spec
    assert ctx.obj.workdir
    assert ctx.obj.output

    gen = SpecGenerator(
        workdir=ctx.obj.workdir,
        output=ctx.obj.output,
        lsp_spec=lsp_spec,
        lsp_repo=lsp_repo,
        lsp_committish=lsp_committish,
        vlspn_repo=vlspn_repo,
        vlspn_committish=vlspn_committish,
    )
    sys.exit(gen.generate())
