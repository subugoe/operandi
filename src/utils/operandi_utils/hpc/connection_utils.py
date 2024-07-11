from paramiko import SFTPClient, SSHClient, Transport


def is_sftp_conn_responsive(logger, sftp_client: SFTPClient) -> bool:
    if not sftp_client:
        logger.warning("The sftp client is non-existing")
        return False
    channel = sftp_client.get_channel()
    if not channel:
        logger.warning("The sftp client channel is non-existing")
        return False
    return is_transport_responsive(logger, channel.get_transport())


def is_ssh_conn_responsive(logger, ssh_client: SSHClient) -> bool:
    if not ssh_client:
        logger.warning("The ssh client is non-existing")
        return False
    return is_transport_responsive(logger, ssh_client.get_transport())


def is_transport_responsive(logger, transport: Transport) -> bool:
    if not transport:
        logger.warning("The transport is non-existing")
        return False
    if not transport.is_active():
        logger.warning("The transport is non-active")
        return False
    try:
        # Sometimes is_active() returns false-positives, hence the extra check
        transport.send_ignore()
        # Nevertheless this still returns false-positives...!!!
        # https://github.com/paramiko/paramiko/issues/2026
        return True
    except EOFError as error:
        logger.error(f"is_transport_responsive EOFError: {error}")
        return False
