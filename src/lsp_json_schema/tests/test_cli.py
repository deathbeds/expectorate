from click.testing import CliRunner

from ..cli import __version__, cli


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip().endswith(__version__)
