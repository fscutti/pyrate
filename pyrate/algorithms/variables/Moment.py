""" Calculates the nth moment of a waveform, treating the waveform as a  over
    the passed in window range
    Momrnt = sum(x_i - mu)^n/N / stddev^n

    

    Required parameters:
        order: (int) The order of the moment. e.g. order 3 for skewness,
                      order 4 for kurtosis
        rate: (float) The digitisation rate

    
    Optional parameters:
        excess: (bool) Implements the excess definition of kurtosis (order 4)
                       Excess kurtosis = 4th Moment - 3
                       Default setting is True
   

    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    

    Example config:

    
    Skew_CHX:
        algorithm:
            name: Moment
            order: 3
            rate: 500e6
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

import sys
import math
from pyrate.core.Algorithm import Algorithm


class Moment(Algorithm):
    __slots__ = ("order", "excess", "time_period", "length", "samples")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):

        """Prepares the config order of the moment"""
        if "order" not in self.config["algorithm"]:
            sys.exit("ERROR: in config, Moment algorithm requires a order parameter")
        self.order = int(self.config["algorithm"]["order"])

        self.excess = True
        if "excess" in self.config["algorithm"]:
            self.excess = bool(self.config["algorithm"]["excess"])

        self.time_period = 1 / float(self.config["algorithm"]["rate"])
        self.length = None
        self.samples = None

    def execute(self):

        """Calculates the nth order moment"""
        waveform = self.store.get(self.config["waveform"])
        window = self.store.get(self.config["window"])
        # Hacky way to get the time bin mids to be used
        # Not in initialise cause we don't know the length at that stage
        ########################################################################
        if self.length is None or self.samples is None:
            self.length = len(waveform)
            # Time shifted to middle of bin
            self.samples = [
                i * self.time_period + self.time_period / 2 for i in range(self.length)
            ]
        ########################################################################
        if window is None or window == -999:
            Moment = -999
        else:
            # First, have to make the waveform positive definite
            min_val = min(waveform)
            entries = [
                x - min_val for x in waveform[window[0] : window[1]]
            ]  # place the minimum value at 0 volts/ADC
            bin_mids = self.samples[window[0] : window[1]]  # Make them bin mids

            # Calculate mean and variance
            entry_sum = sum(entries)
            if entry_sum == 0:
                Moment = -999
            else:
                mean = (
                    sum([i * j for i, j in zip(entries, bin_mids)]) / entry_sum
                )  # Have I made a typo here? Should it be / N ?
                shifted_mids = [i - mean for i in bin_mids]
                variance = (
                    sum([i * math.pow(j, 2) for i, j in zip(entries, shifted_mids)])
                    / entry_sum
                )

                Mn = (
                    sum(
                        [
                            i * math.pow(j, self.order)
                            for i, j in zip(entries, shifted_mids)
                        ]
                    )
                    / entry_sum
                )
                Moment = Mn / math.pow(
                    variance, self.order / 2.0
                )  # /2.0 because using variance instead of std dev

                if self.excess and self.order == 4:
                    # Excess definition of Kurtosis, minus 3 because reasons
                    Moment -= 3

        self.store.put(self.name, Moment)


# EOF
