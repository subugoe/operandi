import click

__all__ = ['cli']

from .harvest import harvester_cli

@click.group()
@click.version_option()
def cli(**kwargs): # pylint: disable=unused-argument
    """
    Entry-point of multi-purpose CLI for Harvester
    """

cli.add_command(harvester_cli)
