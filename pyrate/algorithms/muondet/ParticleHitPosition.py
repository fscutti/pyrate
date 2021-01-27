""" Retrive x,y,z vertex position.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class ParticleHitPosition(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        coor = config["algorithm"]["coordinate"]

        pos = None

        if coor == "x":
            pos = self.store.get("EVENT:TotT:XPosTot")[0]

        if coor == "y":
            pos = self.store.get("EVENT:TotT:YPosTot")[0]

        if coor == "z":
            pos = self.store.get("EVENT:TotT:ZPosTot")[0]

        self.store.put(config["name"], pos)


# EOF
