import click

# ----------------------------------------------------------------------
# operandi-broker broker
# ----------------------------------------------------------------------


@click.group("broker")
def broker_cli():
    """
    Broker related cli
    """


@broker_cli.command('start')
def start_broker():
    print(f"Started broker.")


@broker_cli.command('stop')
def stop_server():
    print(f"Stopped broker.")
