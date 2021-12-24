""" Gets the peak height of the waveform
    Currently just naively gets the maximum value of the entire trace
    PeakHeight = max(trace)

    Required parameters:
        waveform: A waveform for which the maximum value will be calculated
    
    Required states:
        execute:
            input: <Waveform object>
            output: SELF
    
    Example config:

    PeakHeight_CHX:
        algorithm:
            name: PeakHeight
        execute:
            input: CorrectedWaveform_CHX
            output: SELF
        waveform: CorrectedWaveform_CHX
"""

from pyrate.core.Algorithm import Algorithm

class PeakHeight(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        """ Caclulates the waveform peak height (maximum)
        """
        waveform = self.store.get(config["waveform"])
        PeakHeight = max(waveform)
        self.store.put(config['name'], PeakHeight)

# EOF