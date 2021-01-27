""" Compute average energy in input bins.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class TrueEnergy(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        te = self.store.get("EVENT:nT:ekin_particle")[0]

        self.store.put(config["name"], te)


# EOF
