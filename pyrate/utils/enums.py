""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    SKIP_WRITE = 1  # Tells the Run to skip writing for a target
    NONE = 2  # A None object for internal pyrate use
    SKIP_NEXT_STATE = (
        3  # Tells the Run to skip launching the next state for this target
    )
