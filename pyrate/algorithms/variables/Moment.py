""" Calculates the nth moment of a waveform, treating the waveform as a pdf
    

    Required parameters:
        degree: (int) The degree/order of the moment. e.g. degree 3 for skewness,
                      degree 4 for kurtosis
        rate: (float) The digitisation rate
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:
    
    Skew_CHX:
        algorithm:
            name: Moment
            degree: 3
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
    __slots__ = ('degree', 'time_period', 'length', 'time')

    def __init__(self, name, config, store, logger):
        super().__init__(self, name, config, store, logger)

    def initialise(self):
        """ Prepares the config degree of the moment
        """
        if "degree" not in self.config:
            sys.exit("ERROR: in config, Moment algorithm requires a degree parameter")
        self.degree = int(self.config["algorithm"]["degree"])

        self.time_period = 1/float(self.config["algorithm"]["rate"])
        self.length = None
        self.time = None

    def execute(self):
        """ Calculates the nth degree moment
        """
        waveform = self.config["waveform"]
        window = self.config["window"]
        # Hacky way to get the time bin mids to be used
        ########################################################################
        if self.length is None or self.time is None:
            self.length = len(waveform)
            # Time shifted to middle of bin
            self.time = [i * self.time_period + self.time_period/2 for i in range(self.length)]
        ########################################################################
        if window is None or window == -999:
            Moment = -999
        else:
            # First, have to make the waveform positive definite
            min_val = min(waveform)
            entries = [x - min_val for x in waveform[window[0]:window[1]]] # place the minimum value at 0 volts/ADC
            bin_mids = self.time[window[0], window[1]] # Make them bin mids

            # Calculate mean and variance
            entry_sum = sum(entries)
            mean = sum([i*j for i,j in zip(entries, bin_mids)]) / entry_sum # Have I made a typo here? Should it be / N ?
            shifted_mids = [i-mean for i in bin_mids]
            variance = sum([i*math.pow(j,2) for i, j in zip(entries, shifted_mids)]) / entry_sum

            Mn = sum([i * math.pow(j, self.degree) for i, j in zip(entries, shifted_mids)]) / entry_sum
            Moment = Mn / math.pow(variance, self.degree/2.0)
        
        self.store.put(self.name, Moment)

# EOF