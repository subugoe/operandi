import click

from .harvester import Harvester


__all__ = ['cli']


# ----------------------------------------------------------------------
# operandi-harvester
# ----------------------------------------------------------------------
@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Harvester
    """


@cli.command('start')
@click.option('-l', '--limit', default=1, help='The amount of mets files to be harvested.')
def start_harvesting(limit):
    harvester = Harvester()
    print(f"Harvesting started with limit:{limit}")
    harvester.start_harvesting(limit)


# TODO: Not functional yet
"""
@harvester_cli.command('stop')
def stop_harvesting():
  print(f"Stopped harvesting.")
"""
