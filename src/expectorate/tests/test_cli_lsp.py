import json
from pathlib import Path

import jsonschema
import pytest

from ..cli import cli
from .conftest import GOOD_LSP


def assert_generated(workdir: Path, output: Path, version="3.14") -> Path:
    """ helper to check some files after running the generator
    """
    assert (workdir / "language-server-protocol").exists()
    assert (workdir / "vscode-languageserver-node").exists()
    schema = output / f"lsp.{version}.synthetic.schema.json"
    assert schema.exists()
    return schema


def assert_fixtures(schema: Path):
    validator = jsonschema.validators.Draft7Validator(json.loads(schema.read_text()))
    errors = {}
    for name, header_data in GOOD_LSP.items():
        header, data = header_data
        try:
            validator.validate(data)
        except jsonschema.ValidationError as err:
            errors[name] = err
    assert not errors


def test_lsp_cli_default(runner_with_args_and_paths):
    """ happy day, using pre-validated commits from `constants.py`
    """
    runner, args, workdir, output = runner_with_args_and_paths
    result = runner.invoke(cli, [*args, "lsp"], catch_exceptions=False)
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
    final_args = [*args, "lsp", *extra_args]
    result = runner.invoke(cli, final_args, catch_exceptions=False)
    assert result.exit_code == 0, result.__dict__

    spec_version = "3.14"

    if "--lsp-spec-version" in final_args:
        spec_version = final_args[final_args.index("--lsp-spec-version") + 1]

    schema = assert_generated(workdir, output, spec_version)

    assert_fixtures(schema)
