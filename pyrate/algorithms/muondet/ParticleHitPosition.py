""" Retrive x,y,z vertex position.
"""

from pyrate.core.Algorithm import Algorithm


class ParticleHitPosition(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):

        coor = self.config["coordinate"]

        pos = None

        if coor == "x":
            pos = self.store.get(self.config["input"]["xpos"])[0]

        if coor == "y":
            pos = self.store.get(self.config["input"]["ypos"])[0]

        if coor == "z":
            pos = self.store.get(self.config["input"]["zpos"])[0]

        self.store.put(self.name, pos)


# EOF
