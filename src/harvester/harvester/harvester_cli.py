import click
from .harvester import Harvester


__all__ = ['cli']


# ----------------------------------------------------------------------
# perandi-harvester
# ----------------------------------------------------------------------
@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Harvester
    """


@cli.command('start')
@click.option('-l', '--limit', default=1,
              help='The amount of mets files to be harvested.')
@click.option('-a', '--address', required=True,
              default='http://localhost:8000',
              help='The address of the Operandi Server.')
def start_harvesting(limit, address):
    harvester = Harvester(server_address=address)
    harvester.start_harvesting(limit)


# TODO: Not functional yet
"""
@harvester_cli.command('stop')
def stop_harvesting():
  print(f"Stopped harvesting.")
"""
