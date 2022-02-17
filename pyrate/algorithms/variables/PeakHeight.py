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
            window: True
        execute:
            input: CorrectedWaveform_CHX, Window
        waveform: CorrectedWaveform_CHX
        window: Window

"""

from pyrate.core.Algorithm import Algorithm


class PeakHeight(Algorithm):
    __slots__ = "use_window"

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Allows the user to determine if the peak is in a smaller window"""
        self.use_window = False
        if "window" in self.config["algorithm"]:
            self.use_window = bool(self.config["algorithm"]["window"])

    def execute(self):
        """Caclulates the waveform peak height (maximum)"""
        waveform = self.store.get(self.config["waveform"])
        window = self.store.get(self.config["window"])
        if window == -999 or window == None:
            PeakHeight = -999
        else:
            PeakHeight = max(waveform[window[0] : window[1]])

        self.store.put(self.name, PeakHeight)


# EOF