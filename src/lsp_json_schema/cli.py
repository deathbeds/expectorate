from pathlib import Path

import click

from ._version import __version__
from .api import Generator

# from typing import Optional, Text


@click.command()
@click.version_option(__version__)
@click.option("--workdir", "-w", default=Path.cwd() / "work", type=Path)
@click.option("--output", "-o", default=Path.cwd() / "output", type=Path)
def cli(workdir: Path, output: Path) -> int:
    """ lsp-json-schema
    """
    gen = Generator(workdir=workdir, output=output)
    gen.generate()
    return 0
