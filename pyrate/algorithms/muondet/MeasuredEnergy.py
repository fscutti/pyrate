""" Compute average energy in input bins.
"""
import sys
from copy import copy

import ROOT as R

# import numpy as np

from pyrate.core.Algorithm import Algorithm


class MeasuredEnergy(Algorithm):
    #__slots__ = ("quantum_efficiency")

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

        self.quantum_efficiency = copy(R.TH1F("quantum_efficiency","quantum_efficiency", 6, 200, 800))
        self.quantum_efficiency.Fill(250, 0)
        self.quantum_efficiency.Fill(350, 21)
        self.quantum_efficiency.Fill(450, 25)
        self.quantum_efficiency.Fill(550, 10)
        self.quantum_efficiency.Fill(650, 1)
        self.quantum_efficiency.Fill(750, 0.001)

    def execute(self, config):

        wf = self.store.get(config["waveform"])

        measured_energy = 0.0
        e_num, e_den = 0.0, 0.0

        for e, t in zip(wf["energy"], wf["time"]):

            bin_idx = self.quantum_efficiency.GetXaxis().FindBin(self.photon_wavelength(e))

            if "only_photons" in config["algorithm"]:
                if config["algorithm"]["only_photons"]:
                    e_num += t * self.quantum_efficiency.GetBinContent(bin_idx) / 100.0
            else:
                e_num += e * t

            # e_num += e
            e_den += t

        if e_den > 0.0:
            measured_energy = e_num / e_den
        #else: 
        #    measured_energy = e_num
        
        self.store.put(config["name"], measured_energy)

    def photon_wavelength(self, energy, eunits=1e6):

        hc = 1.2398e3  # eV * nm

        return hc / (energy * eunits)


# EOF
