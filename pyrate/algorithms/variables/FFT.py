""" Calculates the fast Fourier transform of a waveform, or window of a waveform.
    Transform is found by using the numpy rfft (real fast-fourier-transform) function, which returns the 1D fft for real-valued inputs. The resulting fft output is then
    converted into real numbers from the complex valued output, which are then converted into absolute amplitudes.

    Required parameters:
        bins: (int) the range and number of frequency bins
        rate: (float) the sample rate of the digitiser
        waveform: The waveform to caluclate the charge of (typically physcial)
        window: (bool) flag for using windowed mode
        window: (tuple) The start and stop window for calculating the charge
    
    Required states:
    NB: <Window object> can be excluded if not using a window)
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:
    
    (Windowed mode)
    FFT_CHX:
        algorithm:
            name: FFT
            rate: 500e6
            bins: 100
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
    
    (Non-windowed mode)
    FFT_CHX:
        algorithm:
            name: FFT
            rate: 500e6
            bins: 100
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX
        waveform: CorrectedWaveform_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class FFT(Algorithm):
    __slots__ = ("use_window", "sample_rate", "fft_bins")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Allows the user to determine if the FFT is calculated for a window 
        of the waveform"""
        self.use_window = False
        if "window" in self.config:
            self.use_window = True

        self.sample_rate = float(self.config["algorithm"]["rate"])
        self.fft_bins = self.config["algorithm"]["bins"]

    def execute(self):
        """Caclulates the FFT based on the chosen mode"""
        waveform = self.store.get(self.config["waveform"])
        if waveform is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return

        # Checks if window is used
        if self.use_window:
            window = self.store.get(self.config["window"])
        else:
            window = (None, None)

        if window is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return

        # Getting the FFT using numpy functions. FFT for real valued input is 
        # found, and real-valued output obtained and then converted into 
        # absolute values.
        fft_amps = np.fft.rfft(a = waveform[window[0]:window[1]], n = self.fft_bins)
        fft_amps = fft_amps.real
        fft_amps = np.abs(fft_amps)

        fft_freq = np.fft.rfftfreq(n = self.fft_bins)*self.sample_rate

        # Storing fft amplitudes and frequencies as 2D array
        fft = np.array([fft_amps, fft_freq])

        self.store.put(self.name, fft)
        

# EOF