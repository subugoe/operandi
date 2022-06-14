import click

__all__ = ['har_cli']

from .harvest import harvester_cli

@click.group()
@click.version_option()
def har_cli(**kwargs): # pylint: disable=unused-argument
    """
    Entry-point of multi-purpose CLI for Harvester
    """

har_cli.add_command(harvester_cli)
