""" An average of all the waveforms from a single channel over the run
    Sums all the waveforms for a single channel and divides by the number of 
    events. Stores in a numpy array, and finishes it in finalise

    Required inputs:
        waveform: A waveform object

    Example config:
    
    AverageWaveform_CHX:
        algorithm: AverageWaveform
        input:
            waveform: CorrectedWaveform_CHX

    Todo:
        1. Decide if the number of events 'nevents' should be pre-calcualted,
           or summed up over execute. Currently emax is just -1...
        2. Replace the messy RecordLength getting code once the reader inputs 
           are unified
        3. How we represent missing channels in an event with multiple channels may change, 
           so the corresponding check will need to be updated in such a situation (LINE 82)
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class AverageWaveform(Algorithm):
    """ Makes a cummulative waveform in the finalise method
    """
    __slots__ = ('nevents', 'cum_waveform')

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """ Create entry for the cummulative waveform structure
        """
        self.nevents = 0
        self.cum_waveform = np.array([])

    def execute(self, condition=None):
        """ Calculates the baseline corrected waveform
        """
        waveform = self.store.get(self.config["input"]["waveform"])

        if waveform is Pyrate.INVALID_VALUE:
            self.put_invalid()
            return
        
        # Handles the case when a channel wasn't present in the event - specific to ZLE and PSD firmware which don't collect waveforms in that case
        # ToDo: How we represent missing channels may change, so this check will need to be updated in such a situation

        # Only runs if the waveform isn't empty
        if waveform.size > 1:
            if self.cum_waveform.size < waveform.size:
                self.cum_waveform = np.zeros(waveform.size)

            self.cum_waveform += waveform
            # If you dont trust emax - emin
            self.nevents += 1

    def finalise(self, condition=None):
        """ Divides cum_waveform by number of events
        """
        AverageWaveform = self.cum_waveform / self.nevents
        self.store.save(self.name, AverageWaveform)

# EOF
