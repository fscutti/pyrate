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
        if window is None or window == -999:
            Moment = -999
        else:
            # First, have to make the waveform positive definite
            min_val = min(waveform)
            entries = [x - min_val for x in waveform[window[0]:window[1]]] # place the minimum value at 0 volts
            bin_mids = npwaveform["time"][window[0], window[1]]

            # Calculate mean and variacne
            mean = np.sum(entries*bin_mids) / np.sum(entries) # Have I made a typo here? Should it be / N ?
            variance = np.sum(entries*math.pow(bin_mids-mean, 2)) /  np.sum(entries)

            Mn = np.sum(entries*math.pow(bin_mids-mean, self.degree)) /  np.sum(entries)
            Moment = Mn / math.pow(variance, self.degree/2.0)
        return Moment

# EOF