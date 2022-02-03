""" Calculates the difference between two times
    dt = time2 - time1
    Where typically time1 is the initial time, and time2 would be the final

    Required parameters:
        time1: (float) The first time (object)
        time2: (float) The second time (object)
    
    Required states:
        execute:
            input: <Time 1 object>, <Time 2 object>
    
    Example config:

    TimeDifference_CH01:
        algorithm:
            name: TimeDifference
        execute:
            input: PulseTime_CH0, PulseTime_CH1
        time1: PulseTime_CH0
        time2: PulseTime_CH1
"""

from pyrate.core.Algorithm import Algorithm

class TimeDifference(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        """ Caclulates the time difference time2 - time1
        """
        t1 = self.store.get(config["time1"])
        t2 = self.store.get(config["time2"])
        TimeDiff = t2-t1
        self.store.put(config["name"], TimeDiff)

# EOF