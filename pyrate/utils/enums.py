""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    NONE = 0            # A None object for internal pyrate core use.
    WRITTEN = 1         # Tells the Run to skip writing for a target.
