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
seconds_to_unit = {"s": 1.0, "ms": 1e3, "us": 1e6, "ns": 1e9, "ps": 1e12}


class TimeConverter(Algorithm):
    __slots__ = "time_conversion"

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Set up time conversion parameters"""
        # Time units
        time_unit = self.config["algorithm"]["unit"]
        if type(time_unit) == str:
            unit = seconds_to_unit[time_unit]
        else:
            unit = float(time_unit)
        sample_rate = float(self.config["algorithm"]["rate"])

        self.time_conversion = unit / sample_rate

    def execute(self):
        """Converts the sample time to physical units"""
        sample_time = self.store.get(self.config["time"])
        real_time = sample_time * self.time_conversion
        self.store.put(self.name, real_time)


# EOF
