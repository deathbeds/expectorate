from pathlib import Path

import pytest
from click.testing import CliRunner

from ..cli import cli


def assert_generated(workdir: Path, output: Path, version="3.14"):
    """ helper to check some files after running the generator
    """
    assert (workdir / "language-server-protocol").exists()
    assert (workdir / "vscode-languageserver-node").exists()
    assert (output / f"lsp.{version}.synthetic.schema.json").exists()


@pytest.fixture
def runner_with_args_and_paths(tmp_path: Path):
    """ wrap up some things used for click testing
    """
    runner = CliRunner()
    workdir = tmp_path / "work"
    output = tmp_path / "output"
    args = ["--workdir", str(workdir), "--output", str(output), "lsp"]
    return runner, args, workdir, output


def test_lsp_cli_default(runner_with_args_and_paths):
    """ happy day, using pre-validated commits from `constants.py`
    """
    runner, args, workdir, output = runner_with_args_and_paths
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0, result.__dict__
    assert_generated(workdir, output)


excursions = {
    "master": ["--lsp-committish", "gh-pages", "--vlspn-committish", "master"],
}

excursions["3.15"] = [*excursions["master"], "--lsp-spec-version", "3.15"]


@pytest.mark.parametrize("label,extra_args", excursions.items())
def test_lsp_cli_args(label, extra_args, runner_with_args_and_paths):
    """ try parsing a number of combinations of relevant combinations
    """
    runner, args, workdir, output = runner_with_args_and_paths
    final_args = [*args, *extra_args]
    result = runner.invoke(cli, final_args, catch_exceptions=False)
    assert result.exit_code == 0, result.__dict__

    spec_version = "3.14"

    if "--lsp-spec-version" in final_args:
        spec_version = final_args[final_args.index("--lsp-spec-version") + 1]

    assert_generated(workdir, output, spec_version)
