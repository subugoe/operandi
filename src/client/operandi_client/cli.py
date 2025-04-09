from click import group, version_option

__all__ = ["cli"]


@group()
@version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Client
    """
