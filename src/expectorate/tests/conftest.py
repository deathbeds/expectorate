from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner_with_args_and_paths(tmp_path: Path):
    """ wrap up some things used for click testing
    """
    runner = CliRunner()
    workdir = tmp_path / "work"
    output = tmp_path / "output"
    args = ["--workdir", str(workdir), "--output", str(output)]
    return runner, args, workdir, output
