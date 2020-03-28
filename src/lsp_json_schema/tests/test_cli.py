# import traceback
from pathlib import Path

from click.testing import CliRunner

from ..cli import __version__, cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip().endswith(__version__)


def test_cli_default(tmp_path: Path):
    runner = CliRunner()
    workdir = tmp_path / "work"
    output = tmp_path / "output"
    args = ["--workdir", str(workdir), "--output", str(output)]
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0, result.__dict__
    assert (workdir / "language-server-protocol").exists()
    assert (workdir / "vscode-languageserver-node").exists()
    assert (output / "lsp.3.14.synthetic.schema.json").exists()
