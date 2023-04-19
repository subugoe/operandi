try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    from importlib_metadata import distribution as get_distribution

__all__ = [
    "OPERANDI_VERSION"
]

OPERANDI_VERSION = get_distribution('operandi_utils').version
