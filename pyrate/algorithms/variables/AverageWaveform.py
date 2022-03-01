""" An average of all the waveforms from a single channel over the run
    Sums all the waveforms for a single channel and divides by the number of 
    events. Stores in a numpy array, and finishes it in finalise

    Required parameters:
        waveform: A waveform object
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>
        finalise:
            output:

    Example config:
    
    AverageWaveform_CHX:
        algorithm:
            name: AverageWaveform
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX
        finalise:
            output:
        waveform: CorrectedWaveform_CHX

    Todo:
        1. Decide if the number of events 'nevents' should be pre-calcualted,
           or summed up over execute. Currently emax is just -1...
        2. Replace the messy RecordLength getting code once the reader inputs 
           are unified
"""

from pyrate.core.Algorithm import Algorithm
import numpy as np

class AverageWaveform(Algorithm):
    """ Makes a cummulative waveform in the finalise method
    """
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """ Create entry for the cummulative waveform structure
        """
        # Todo: replace this pile of code with a simple recordlength getter 
        #       once the reader inputs have been unified.
        
        # All this just to get the record length
        # First we find out what kind of grouping is being used
        groups = ['0']

        # Temporary, needs fixing, not generalised for all possible group structures
        if groups[0] == '0':
            # Default, no group specified
            reader = self.store.get("INPUT:READER:name")
        else:
            reader = self.store.get(f"INPUT:READER:GROUP:name")
        if reader == "ReaderBlueTongueMMAP":
            board_dict = self.store.get(f"INPUT:board_1") # This needs to be fixed when we have more boards 
            RecordLength = board_dict["record_length"]
        elif reader == "ReaderWaveDumpMMAP":
            RecordLength = self.store.get(f"INPUT:Record Length")
        elif reader == "ReaderWaveCatcherMMAP":
            RecordLength = int(self.store.get(f"INPUT:DATA SAMPLES"))
        
        # nevents = 1 + self.store.get("INPUT:config")["eslices"]["emax"] - self.store.get("INPUT:config")["eslices"]["emin"]
        nevents = 0
        self.store.put(f"{self.name}:nevents", nevents)
        self.store.put(f"{self.name}:cum_waveform", np.zeros(RecordLength))

    def execute(self):
        """ Calculates the baseline corrected waveform
        """
        nevents = self.store.get(f"{self.name}:nevents", "PERM")
        waveform = self.store.get(self.config["waveform"]) # Because pyrate broke
        cum_waveform = self.store.get(f"{self.name}:cum_waveform")
        cum_waveform += waveform
        # If you dont trust emax - emin
        nevents = self.store.get(f"{self.name}:nevents") + 1
        # replace=True properly updates the object in the store. "PERM" required here.
        self.store.put(f"{self.name}:nevents", nevents, "PERM", replace=True)
        self.store.put(f"{self.name}:cum_waveform", cum_waveform, "PERM", replace=True)

    def finalise(self):
        """ Divides cum_waveform by number of events
        """
        cum_waveform = self.store.get(f"{self.name}:cum_waveform")
        nevents = self.store.get(f"{self.name}:nevents")
        AverageWaveform = cum_waveform / nevents
        self.store.put(self.name, AverageWaveform)
# EOF