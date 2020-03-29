from pathlib import Path

import click

from ._version import __version__
from .context import Context, ExpectorateContext
from .lsp.cli import lsp


@click.group()
@click.version_option(__version__)
@click.option("--workdir", "-w", default=Path.cwd() / "work", type=Path)
@click.option("--output", "-o", default=Path.cwd() / "output", type=Path)
@click.pass_context
def cli(
    ctx: Context, workdir: Path, output: Path,
):
    """ expectorate
    """
    ctx.ensure_object(ExpectorateContext)

    ctx.obj.workdir = workdir
    ctx.obj.output = output


cli.add_command(lsp)
