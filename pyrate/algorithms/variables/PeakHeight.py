""" Gets the peak height of the waveform
    Currently just naively gets the maximum value of the entire trace
    PeakHeight = max(trace)

    Required inputs:
        waveform: A waveform for which the maximum value will be calculated

    Optional parameters:
        window: A sub window to search for the peak over
    
    Example config:

    PeakHeight_CHX:
        algorithm: PeakHeight
        input:
            waveform: CorrectedWaveform_CHX
            window: Window

"""
import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class PeakHeight(Algorithm):
    __slots__ = "use_window"

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """Allows the user to determine if the peak is in a smaller window"""
        self.use_window = False
        if "window" in self.config:
            self.use_window = True

    def execute(self, condition=None):
        """Caclulates the waveform peak height (maximum)"""
        waveform = self.store.get(self.config["input"]["waveform"])
        if self.use_window:
            window = self.store.get(self.config["input"]["window"])
        else:
            window = (None, None)
        

        if window is Pyrate.NONE or waveform is Pyrate.NONE:
            return

        PeakHeight = np.max(waveform[window[0] : window[1]])
        self.store.put(self.name, PeakHeight)


# EOF