""" Trigger requirements.
"""

from pyrate.core.Algorithm import Algorithm


class Trigger(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        # print("Calling: ", config["name"])
        tmp = self.store.get(config["triggeredch"])
        # print(f"This is a read {tmp}")
        # print(self.store.check("any", "TRAN"))

        # do something here ...
        # tmp = func(tmp)

        self.store.put(config["name"], tmp)


# EOF
