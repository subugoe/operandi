import click

__all__ = ['cli']

from .server import server_cli


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Server
    """


cli.add_command(server_cli)
