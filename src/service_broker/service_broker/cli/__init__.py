import click

__all__ = ['cli']

from .broker import broker_cli


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Broker
    """


cli.add_command(broker_cli)
