""" Calculates the leading edge threshold crossing point for a waveform.
    Outputs the crossing point time minus a user-defined offset.

    Required parameters:
        offset: (int)   The amount that will be subtracted from the threshold crossing point
                        to define the start of the waveform
        threshold: (float) The minimum height the waveform must cross before a starting point is saved
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>
    
    Example configs:

    LeadingEdge_CHX:
        algorithm:
            name: LeadingEdgeThreshold
            offset: 5
            threshold: 5
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX
        waveform: CorrectedWaveform_CHX
"""

from pyrate.core.Algorithm import Algorithm
import numpy as np


class LeadingEdgeThreshold(Algorithm):
    __slots__ = ("offset", "threshold")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Set up the CFD and trapezoid parameters"""
        # offset parameter decides offset from threshold crossing point
        self.offset = int(self.config["algorithm"]["offset"])
        self.threshold = self.config["algorithm"]["threshold"]

    def execute(self):
        """Caclulates the waveform threshold crossing point"""
        # Get the actual waveform, finally.
        waveform = self.store.get(self.config["waveform"])

        threshold_cross_list = waveform[waveform > self.threshold]
        if threshold_cross_list.size>0:
            threshold_cross_idx = np.where(threshold_cross_list[0]==waveform)
            LeadingEdgeTime = threshold_cross_idx[0][0] - self.offset
        else:
            LeadingEdgeTime = -999

        self.store.put(self.name, LeadingEdgeTime)


# EOF