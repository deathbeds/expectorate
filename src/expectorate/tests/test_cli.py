from pathlib import Path

import pytest
from click.testing import CliRunner

# from .. import constants
from ..cli import __version__, cli


def test_version():
    """ smoke test the cli
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip().endswith(__version__)
