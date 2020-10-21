""" Trigger requirements.
"""

from pyrate.core.Algorithm import Algorithm


class Trigger(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        time = self.store.get(config["triggeredch"])

        if "get_diff" in config["algorithm"]:

            # WARNING: since we are using config["name"] to retrieve an object,
            # and config["name"] corresponds to the name of *this* object, we first
            # have to check if the object is on the store already to avoid introducing
            # a circular dependency, as, if it would not be on the store, *this* algorithm
            # will be called recursively. Note that the choice of using config["name"] to compute the
            # variable is completely arbitrary here, and has been chosen only
            # as an example of avoiding circular dependencies with check, but a better choice
            # of variable name should be chosen, not associated with any object linked to
            # an algorithm in the configuration.
            if self.store.check(config["name"], "PERM"):

                previous_time = self.store.get(config["name"], "PERM")

                # NB: this refreshes the value on the permanent store as replace is true.
                self.store.put(config["name"], time, "PERM", replace=True)

                time -= previous_time

            else:
                # NB: this operation will be executed only one time, as we are not forcing a replace.
                self.store.put(config["name"], time, "PERM")

        self.store.put(config["name"], time)


# EOF
