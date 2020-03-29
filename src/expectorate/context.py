import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click


@dataclass
class ExpectorateContext:
    workdir: Optional[Path] = None
    output: Optional[Path] = None
    log: Optional[logging.Logger] = None


class Context(click.Context):
    obj: ExpectorateContext
