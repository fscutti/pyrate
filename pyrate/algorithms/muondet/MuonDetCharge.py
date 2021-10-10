""" Computation of energy deposited.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class MuonDetCharge(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        if config["format"] == "ROOT":

            e = self.store.get(config["edep"])

            self.store.put(config["name"], e)


# EOF
