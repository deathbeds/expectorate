import click

from ._version import __version__


@click.command()
@click.version_option(__version__)
def cli():
    """ lsp-json-schema
    """
    click.echo("Hello World!")
