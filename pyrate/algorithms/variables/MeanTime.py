""" Find the mean time of the waveform in a given window region
    Mean time is calculated using 1/(sample_rate) * sum(A_i * t_i)/sum(A_i)

    Required parameters:
        rate: (float) The sample rate of the digitiser
        
        waveform: The waveform used to calculate the mean time
        window: The window object (tuple) for the calculation region
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:

    MeanTime_CHX:
        algorithm:
            name: MeanTime
            rate: 500e6
        initialise:
            input:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

from pyrate.core.Algorithm import Algorithm

class MeanTime(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        sample_rate = float(config["algorithm"]["rate"])
        self.store.put(f"{config['name']}:sample_rate", sample_rate)

    def execute(self, config):
        waveform = self.store.get(config["waveform"])
        sample_period = 1/self.store.get(f"{config['name']}:sample_rate")
        window = self.store.get(config["window"])
        # check for invalid windows
        if window == -999 or window is None:
            MeanTime = -999
        else:
            num = 0
            denom = 0
            for i in range(0, window[1]-window[0]):
                num += waveform[window[0]+i] * i
                denom += waveform[window[0]+i]
            if denom == 0:
                # print("WARNING: MeanTime denominator = 0, is your window correct?")
                MeanTime = float("inf")
            else:
                MeanTime = sample_period * num/denom
        self.store.put(config["name"], MeanTime)
# EOF