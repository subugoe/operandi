import click
from os import environ
from .harvester import Harvester

__all__ = ['cli']


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Harvester
    """


@cli.command('start')
@click.option('-l', '--limit', default=1,
              help='The amount of mets files to be harvested.')
@click.option('-a', '--address', required=True,
              default='http://localhost:8000',
              help='The address of the Operandi Server.')
def start_harvesting(limit, address):
    if limit > 1:
        raise ValueError("Temporary: the limit cannot be bigger than 1")
    harvester = Harvester(
        server_address=address,
        auth_username=environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME"),
        auth_password=environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD")
    )
    harvester.start_harvesting(limit)


@cli.command('start-dummy')
@click.option('-a', '--address', required=True,
              default='http://localhost:8000',
              help='The address of the Operandi Server.')
def start_harvesting(address):
    harvester = Harvester(
        server_address=address,
        auth_username=environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME"),
        auth_password=environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD")
    )
    harvester.harvest_once_dummy()
