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
from code import interact


class LeadingEdgeThreshold(Algorithm):
    __slots__ = ("offset", "threshold", "interpolate")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Set up the CFD and trapezoid parameters"""
        # offset parameter decides offset from threshold crossing point
        self.offset = int(self.config["algorithm"]["offset"])
        self.threshold = self.config["algorithm"]["threshold"]
        self.interpolate = False
        if "interpolate" in self.config["algorithm"]:
            self.interpolate = True

    def execute(self):
        """Caclulates the waveform threshold crossing point"""
        # Get the actual waveform, finally.
        waveform = self.store.get(self.config["waveform"])

        cross_index = np.argmax(waveform > self.threshold)
        if cross_index:
            if self.interpolate:
                # We want to interpolate between the points
                x1, x2 = cross_index - 1, cross_index
                y1, y2 = waveform[x1], waveform[x2]
                if y1 == y2:
                    # We'll get an invalid value, just want the midpoint
                    LeadingEdgeTime = x1 + 0.5
                else:
                    # Interpolation point = x1 + (y-y1)*(x2-x1)/(y2-y1) ##
                    LeadingEdgeTime = x1 + (self.threshold-y1)/(y2-y1)
            else:
                # We just want the index
                LeadingEdgeTime = cross_index
        else:
            LeadingEdgeTime = -999

        self.store.put(self.name, LeadingEdgeTime-self.offset)


# EOF