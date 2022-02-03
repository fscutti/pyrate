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
            input: CorrectedWaveform_CHX
        waveform: CorrectedWaveform_CHX
"""

from pyrate.core.Algorithm import Algorithm

class PeakLocation(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        """ Caclulates the pulse time based on the mode chosen
        """
        waveform = self.store.get(config["waveform"])
        # Peak location is the highest point on the waveform
        # PeakLocation = np.argmax(waveform)
        PeakLocation = max(range(len(waveform)), key=waveform.__getitem__)
        self.store.put(config["name"], PeakLocation)

# EOF