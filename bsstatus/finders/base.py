"""
Home to the base StatusFinder implementation.
"""

from bsstatus.config import get_config
from bsstatus.status import Status


class StatusFinder:
    """
    A StatusFinder is a class that finds the status of a user from a given source.
    """

    def __init__(self) -> None:
        """
        Initialize the StatusFinder.

        Sets .config to the configuration object.
        """
        self.config = get_config()

    def get_status(self) -> Status:
        """
        Get the current status of the user from the source.
        """
        raise NotImplementedError("Subclasses should implement this method.")
