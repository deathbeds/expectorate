from pathlib import Path

import pytest
from click.testing import CliRunner
from ruamel import yaml

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
LSP_FIXTURES = FIXTURES / "lsp"
GOOD_LSP = {
    p.name: yaml.safe_load_all(p.read_text())
    for p in sorted(LSP_FIXTURES.glob("*_good_*.yaml"))
}


@pytest.fixture
def runner_with_args_and_paths(tmp_path: Path):
    """ wrap up some things used for click testing
    """
    runner = CliRunner()
    workdir = tmp_path / "work"
    output = tmp_path / "output"
    args = ["--workdir", str(workdir), "--output", str(output)]
    return runner, args, workdir, output
