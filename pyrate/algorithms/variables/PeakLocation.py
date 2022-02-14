""" Gets the index of the peak of a waveform, currently set to the maximum
    The current version avoids numpy as uses a neat trick found 
    on stack overflow https://stackoverflow.com/questions/2474015/getting-the-index-of-the-returned-max-or-min-item-using-max-min-on-a-list 

    Required parameters:
        waveform: The waveform for which the maximum will be calculated
    
    Required states:
        execute:
            input: <Waveform object>

    Example config:
    
    PeakLocation_CHX:
        algorithm:
            name: PeakLocation
        execute:
            input: CorrectedWaveform_CHX, Window
        waveform: CorrectedWaveform_CHX
        window: Window
"""

from pyrate.core.Algorithm import Algorithm

class PeakLocation(Algorithm):
    __slots__ = ('use_window')

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
    
    def initialise(self):
        """ Allows the user to determine if the peak is in a smaller window
        """
        self.use_window = False
        if "window" in self.config["algorithm"]:
            self.use_window = bool(self.config["algorithm"]["window"])

    def execute(self):
        """ Caclulates the pulse time based on the mode chosen
        """
        waveform = self.store.get(self.config["waveform"])
        # Peak location is the highest point on the waveform
        # PeakLocation = np.argmax(waveform)
        if self.use_window:
            window = self.store.get(self.config["window"])
        else:
            window = (None, None)
        if window == -999 or window is None:
            PeakLocation = -999
        else:
            PeakLocation = max(range(len(waveform[window[0]:window[1]])), key=waveform.__getitem__)
        self.store.put(self.name, PeakLocation)

# EOF