"""
Home to the Status class.
"""

from enum import IntEnum, auto


class Status(IntEnum):
    """
    Enum representing different status states.

    Order here is important. The order of the states is used to determine
    the precedence of the state. The state with the highest value (latest in the listing)
    that is found from any status finder will be used.
    """

    # No idea
    Unknown = auto()

    # The user is available
    Available = auto()

    # The user is away
    Away = auto()

    # The user is busy
    Busy = auto()

    # The user should not be disturbed
    DoNotDisturb = auto()
