""" Calculates a sum over a region of a waveform
    Sums the waveform over a passed in window object. 

    Required parameters:
        waveform: The waveform to caluclate the sum of (typically physcial)
        window: (tuple) The start and stop window for summing over
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:
    
    Sum_CHX:
        algorithm:
            name: Sum
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

from pyrate.core.Algorithm import Algorithm


class Sum(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """Sum over the waveform"""
        window = self.store.get(self.config["window"])

        # check for invalid windows
        if window == -999 or window is None:
            Sum = -999

        else:
            waveform = self.store.get(self.config["waveform"])

            # Sum the waveform
            Sum = sum(waveform[window[0] : window[1]])

        self.store.put(self.name, Sum)


# EOF
