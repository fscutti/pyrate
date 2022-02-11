""" Calculates the nth moment of a waveform, treating the waveform as a pdf
 
    ### ADD IN FORMULA HERE ###


    Required parameters:
        Add parameters here
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:
    
    Moment3_CHX:
        algorithm:
            name: Moment
            degree: 3
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

from pyrate.core.Algorithm import Algorithm
import math

class Moment(Algorithm):

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self):
        """ Prepares the config degree of the moment
        """
        if "degree" not in self.config:
            sys.exit("ERROR: in config, Moment algorithm requires a degree parameter")
        self.degree = int(self.config["algorithm"]["degree"])

    def execute(self):
        """ Calculates the nth degree moment
        """
        waveform = self.config["waveform"]
        window = self.config["window"]
        # Fix Me 
        ########################################################################
        time = [1,2,3,4,5] # Times or something pu that here 
        ########################################################################
        if window is None or window == -999:
            Moment = -999
        else:
            # First, have to make the waveform positive definite
            min_val = min(waveform)
            entries = [x - min_val for x in waveform[window[0]:window[1]]] # place the minimum value at 0 volts/ADC
            # FIX ME
            ####################################################################
            bin_mids = time[window[0], window[1]] # Make them bin mids
            ####################################################################

            # Calculate mean and variance
            entry_sum = sum(entries)
            mean = sum([i*j for i,j in zip(entries, bin_mids)]) / entry_sum # Have I made a typo here? Should it be / N ?
            shifted_mids = [i-mean for i in bin_mids]
            variance = sum([i*math.pow(j,2) for i, j in zip(entries, shifted_mids)]) / entry_sum

            Mn = sum([i * math.pow(j, self.degree) for i, j in zip(entries, shifted_mids)]) / entry_sum
            Moment = Mn / math.pow(variance, self.degree/2.0)
        return Moment

# EOF