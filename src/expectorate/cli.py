import logging
from pathlib import Path
from typing import Text

import click

from ._version import __version__
from .context import Context, ExpectorateContext
from .lsp.cli import lsp


@click.group()
@click.version_option(__version__)
@click.option("--workdir", "-w", default=Path.cwd() / "work", type=Path)
@click.option("--output", "-o", default=Path.cwd() / "output", type=Path)
@click.option("--log-level", default="INFO")
@click.option("--debug/--no-debug", "-d", default=False)
@click.pass_context
def cli(ctx: Context, workdir: Path, output: Path, log_level: Text, debug: bool):
    """ expectorate
    """
    ctx.ensure_object(ExpectorateContext)

    ctx.obj.workdir = workdir
    ctx.obj.output = output
    log = logging.getLogger(__name__)
    log.setLevel("DEBUG" if debug else log_level)
    ctx.obj.log = log


cli.add_command(lsp)
