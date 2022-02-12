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
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """ Caclulates the pulse time based on the mode chosen
        """
        waveform = self.store.get(self.config["waveform"])
        # Peak location is the highest point on the waveform
        # PeakLocation = np.argmax(waveform)
        window = self.store.get(self.config["window"])
        if window == -999 or window == None:
            PeakLocation = -999
        else:
            PeakLocation = max(range(len(waveform[window[0]:window[1]])), key=waveform.__getitem__)
        self.store.put(self.name, PeakLocation)

# EOF