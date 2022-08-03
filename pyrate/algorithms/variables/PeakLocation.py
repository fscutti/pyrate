""" Gets the index of the peak of a waveform, currently set to the maximum
    The current version avoids numpy as uses a neat trick found 
    on stack overflow https://stackoverflow.com/questions/2474015/getting-the-index-of-the-returned-max-or-min-item-using-max-min-on-a-list 

    Required inputs:
        waveform: The waveform for which the maximum will be calculated

    Optional inputs:
        window: A sub window to search for the peak over

    Example config:
    
    PeakLocation_CHX:
        algorithm: PeakLocation
        input:
            waveform: CorrectedWaveform_CHX
            window: Window
"""
import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class PeakLocation(Algorithm):
    __slots__ = "use_window"

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """Allows the user to determine if the peak is in a smaller window"""
        self.use_window = False
        if "window" in self.config:
            self.use_window = True

    def execute(self, condition=None):
        """Caclulates the pulse time based on the mode chosen"""
        waveform = self.store.get(self.config["input"]["waveform"])
        # PeakHeight = self.store.get(self.config["peakheight"])
        # Peak location is the highest point on the waveform
        # PeakLocation = np.argmax(waveform)
        if self.use_window:
            window = self.store.get(self.config["input"]["window"])
        else:
            window = (None, None)
        if window is Pyrate.NONE or waveform is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return
        
        PeakLocation = np.argmax(waveform[window])
        self.store.put(self.name, PeakLocation)


# EOF

