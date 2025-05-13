"""
Home to the base StatusFinder implementation.

StatusFinders should only get the configs for themselves. They shouldn't
need the configs of other finders or from the main config either.
"""

from bsstatus.config import FinderConfig
from bsstatus.status import Status


class StatusFinder:
    """
    A StatusFinder is a class that finds the status of a user from a given source.
    """

    def __init__(self, finder_config: FinderConfig) -> None:
        """
        Initialize the StatusFinder.

        Sets .config to the configuration object for this finder.
        """
        self.config = finder_config

    def get_status(self) -> Status:
        """
        Get the current status of the user from the source.
        """
        raise NotImplementedError("Subclasses should implement this method.")
