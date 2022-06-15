import click

from harvester.harvester import Harvester


# ----------------------------------------------------------------------
# operandi-harvester harvest
# ----------------------------------------------------------------------

@click.group("harvest")
def harvester_cli():
    """
    Harvesting related cli
    """
    print("Harvesting related cli")


@harvester_cli.command('start')
@click.option('-l', '--limit', default=1, help='The amount of mets files to be harvested.')
def start_harvesting(limit):
    harvester = Harvester()
    print(f"Harvesting started with limit:{limit}")
    harvester.start_harvesting(limit)


@harvester_cli.command('stop')
def stop_harvesting():
    print(f"Stopped harvesting.")
