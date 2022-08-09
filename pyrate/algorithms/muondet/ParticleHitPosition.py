""" Retrive x,y,z vertex position.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class ParticleHitPosition(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):

        coor = self.config["coordinate"]

        pos = None

        if coor == "x":
            pos = self.store.get("EVENT:TotT:XPosTot")[0]

        if coor == "y":
            pos = self.store.get("EVENT:TotT:YPosTot")[0]

        if coor == "z":
            pos = self.store.get("EVENT:TotT:ZPosTot")[0]

        self.store.put(self.name, pos)


# EOF
