from pathlib import Path

import pytest
from click.testing import CliRunner

# from .. import constants
from ..cli import __version__, cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip().endswith(__version__)


def assert_generated(workdir: Path, output: Path, version="3.14"):
    assert (workdir / "language-server-protocol").exists()
    assert (workdir / "vscode-languageserver-node").exists()
    assert (output / f"lsp.{version}.synthetic.schema.json").exists()


@pytest.fixture
def runner_with_args_and_paths(tmp_path: Path):
    runner = CliRunner()
    workdir = tmp_path / "work"
    output = tmp_path / "output"
    args = ["--workdir", str(workdir), "--output", str(output)]
    return runner, args, workdir, output


def test_cli_default(runner_with_args_and_paths):
    runner, args, workdir, output = runner_with_args_and_paths
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0, result.__dict__
    assert_generated(workdir, output)


excursions = {
    "master": ["--lsp-committish", "gh-pages", "--vlspn-committish", "master"],
}


@pytest.mark.parametrize("label,extra_args", excursions.items())
def test_cli_args(label, extra_args, runner_with_args_and_paths):
    runner, args, workdir, output = runner_with_args_and_paths
    final_args = [*args, *extra_args]
    result = runner.invoke(cli, final_args, catch_exceptions=False)
    assert result.exit_code == 0, result.__dict__
    assert_generated(workdir, output)
