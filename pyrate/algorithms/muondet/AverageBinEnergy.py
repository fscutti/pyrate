""" Compute average energy in input bins.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class AverageBinEnergy(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        e = self.store.get("EVENT:nT:edepScint")

        self.store.put(config["name"], e)


# EOF
