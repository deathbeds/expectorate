import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Text, Optional

import click

from . import constants
from ._version import __version__


@dataclass
class Context:
    workdir: Optional[Path]
    output: Optional[Path]


@click.group()
@click.version_option(__version__)
@click.option("--workdir", "-w", default=Path.cwd() / "work", type=Path)
@click.option("--output", "-o", default=Path.cwd() / "output", type=Path)
@click.pass_context
def cli(
    ctx: Context,
    workdir: Path,
    output: Path,
):
    """ expectorate
    """
    ctx.ensure_object(Context)

    ctx.workdir = workdir
    ctx.output = output


# late import to avoid circular ref
from .lsp.cli import lsp
