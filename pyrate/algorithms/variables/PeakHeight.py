""" Gets the peak height of the waveform
    Currently just naively gets the maximum value of the entire trace
    PeakHeight = max(trace)

    Required parameters:
        waveform: A waveform for which the maximum value will be calculated
    
    Required states:
        execute:
            input: <Waveform object>
    
    Example config:

    PeakHeight_CHX:
        algorithm:
            name: PeakHeight
        execute:
            input: CorrectedWaveform_CHX, Window
        waveform: CorrectedWaveform_CHX
        window: Window
"""

from pyrate.core.Algorithm import Algorithm

class PeakHeight(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """ Caclulates the waveform peak height (maximum)
        """
        waveform = self.store.get(self.config["waveform"])
        window = self.store.get(self.config["window"])
        PeakHeight = max(waveform[window[0]:window[1]])
        self.store.put(self.name, PeakHeight)

# EOF