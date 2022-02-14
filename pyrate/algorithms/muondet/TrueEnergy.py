""" Compute average energy in input bins.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class TrueEnergy(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):

        te = self.store.get(self.config["etrue"])[0]

        self.store.put(self.name, te)


# EOF
