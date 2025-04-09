from click import group, option, version_option
from .constants import DEFAULT_OPERANDI_SERVER_ROOT_URL
from .harvester import Harvester

__all__ = ["cli"]


@group()
@version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Harvester
    """


@cli.command("start")
@option(
    "-l", "--limit",
    default=1,
    help="The amount of mets files to be harvested."
)
@option(
    "-a", "--address",
    required=True,
    default=DEFAULT_OPERANDI_SERVER_ROOT_URL,
    help="The address of the Operandi Server."
)
def start_harvesting(limit, address):
    harvester = Harvester(server_address=address)
    harvester.start_harvesting(limit)


@cli.command("start-dummy")
@option(
    "-a", "--address", required=True,
    default=DEFAULT_OPERANDI_SERVER_ROOT_URL,
    help="The address of the Operandi Server."
)
def start_harvesting(address):
    harvester = Harvester(server_address=address)
    harvester.harvest_once_dummy()
