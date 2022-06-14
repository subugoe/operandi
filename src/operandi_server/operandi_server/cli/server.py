import click

# ----------------------------------------------------------------------
# operandi-server server
# ----------------------------------------------------------------------


@click.group("server")
def server_cli():
    """
    Server related cli
    """
    print("Server related cli")


@server_cli.command('start')
def start_server():
    print(f"Started server.")


@server_cli.command('stop')
def stop_server():
    print(f"Stopped server.")
