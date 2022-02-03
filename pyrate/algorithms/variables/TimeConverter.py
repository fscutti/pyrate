""" Converts sample times to real world time units
    Sample times can be floats (interpolated)
    Real time = sample / sample-rate * unit

    Required parameters:
        rate: (float) The sample rate of the digitiser
        unit: (float/string) The desired units of the output time. Choose from
                             the predefined units or specify your own.
        time: (int) The orignal time in units of samples from another object.
    
    Required states:
        initialise:
            output:
        execute:
            input: <Time object>
    
    Example config:

    PulseTime_CHX:
        algorithm:
            name: TimeConverter
            rate: 500e6
            unit: ns
        initialise:
            output:
        execute:
            input: PulseStart_CHX
        time: PulseStart_CHXCFD
"""

from pyrate.core.Algorithm import Algorithm

# Predefined units: seconds, milliseconds, microseconds, nanoseconds and 
# picoseconds. Feel free to add more if they're common.
seconds_to_unit = {"s": 1.0, "ms":1e3, "us":1e6, "ns":1e9, "ps":1e12}

class TimeConverter(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
    
    def initialise(self, config):
        """ Set up time conversion parameters
        """
        # Time units
        time_unit = config["algorithm"]["unit"]
        if type(time_unit) == str:
            unit = seconds_to_unit[time_unit]
        else:
            unit = float(time_unit)
        sample_rate = float(config["algorithm"]["rate"])

        time_conversion = unit/sample_rate
        self.store.put(f"{config['name']}:time_conversion", time_conversion)

    def execute(self, config):
        """ Converts the sample time to physical units
        """
        time_conversion = self.store.get(f"{config['name']}:time_conversion")
        sample_time = self.store.get(config["time"])
        real_time = sample_time * time_conversion
        self.store.put(config['name'], real_time)

# EOF