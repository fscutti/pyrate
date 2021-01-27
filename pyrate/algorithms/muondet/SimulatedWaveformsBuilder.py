""" Build simulated waveform.
"""
import sys
from copy import copy

import numpy as np

from pyrate.core.Algorithm import Algorithm

class SimulatedWaveformsBuilder(Algorithm):
    __slots__ = ("pmt_map", "pmt_intervals", "pc_width", "pc_depth")

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

        self.pc_width = 60.0
        self.pc_depth = 40.0

        self.pmt_map = {
            "PMT1": None,
            "PMT2": None,
            "PMT3": None,
            "PMT4": None,
            "PMT5": None,
            "PMT6": None,
            "PMT7": None,
            "PMT8": {"x": 1700.0, "y": 0.0, "z": -830.0},
            "PMT9": {"x": -1700.0, "y": 0.0, "z": -830.0},
            "PMT10": None,
            "PMT11": None,
            "PMT12": {"x": 1700.0, "y": 0.0, "z": 0.0},
            "PMT13": {"x": -1700.0, "y": 0.0, "z": 0.0},
        }

        self.pmt_intervals = {}
        for pmt, position in self.pmt_map.items():

            if not position:
                continue

            self.pmt_intervals[pmt] = {}
            self.pmt_intervals[pmt]["x"] = [
                position["x"] - self.pc_depth,
                position["x"] + self.pc_depth,
            ]
            self.pmt_intervals[pmt]["y"] = [
                position["y"] - self.pc_width,
                position["y"] + self.pc_width,
            ]
            self.pmt_intervals[pmt]["z"] = [
                position["z"] - self.pc_width,
                position["z"] + self.pc_width,
            ]

    def execute(self, config):
        
        waveforms = {}
        for pmt, position in self.pmt_intervals.items():
            waveforms[pmt] = {"energy": [], "time": []}
        
        x_hits = self.store.get(config["algorithm"]["hits_x_positions"])
        y_hits = self.store.get(config["algorithm"]["hits_y_positions"])
        z_hits = self.store.get(config["algorithm"]["hits_z_positions"])

        energy_hits = self.store.get(config["algorithm"]["energy"])
        time_hits = self.store.get(config["algorithm"]["time"])

        for pmt, position in self.pmt_intervals.items():
            for idxHit, (x, y, z) in enumerate(zip(x_hits, y_hits, z_hits)):

                if self.hitIsCompatible((x, y, z), position):

                    waveforms[pmt]["energy"].append(energy_hits[idxHit])
                    waveforms[pmt]["time"].append(time_hits[idxHit])

        self.store.put(config["name"], waveforms)

    def hitIsCompatible(self, hit_position, interval):
        """Check if the position of the hit is compatible with a given PMT photocathode position."""

        if hit_position[0] < interval["x"][0]:
            return False
        if hit_position[0] >= interval["x"][1]:
            return False

        if hit_position[1] < interval["y"][0]:
            return False
        if hit_position[1] >= interval["y"][1]:
            return False

        if hit_position[2] < interval["z"][0]:
            return False
        if hit_position[2] >= interval["z"][1]:
            return False

        return True


# EOF
