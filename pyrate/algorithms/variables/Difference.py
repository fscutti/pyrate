""" Calculates the difference between two variables
    dx = x2 - x1
    Where typically x1 is the initial variable, and x2 would be the final
    e.g. x1 = initial time, x2 = final time

    Required parameters:
        x1: (number) The first numerical (object)
        x2: (number) The second numerical (object)
    
    Required states:
        execute:
            input: <Number object 1>, <Number object 2>
    
    Example config:

    TimeDifference_CH01:
        algorithm:
            name: Difference
        execute:
            input: PulseTime_CH0, PulseTime_CH1
        x1: PulseTime_CH0
        x2: PulseTime_CH1
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class Difference(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """Caclulates the time difference time2 - time1"""
        x1 = self.store.get(self.config["x1"])
        x2 = self.store.get(self.config["x2"])
        if x1 is Pyrate.NONE or x2 is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return
        Diff = x2 - x1
        self.store.put(self.name, Diff)


# EOF
