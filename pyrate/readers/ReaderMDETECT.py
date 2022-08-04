""" Reader of an mDetect file containing field data.
"""
import os
from copy import copy

import mmap

# import linecache

import sys

import h5py as H
import pandas as pd

from pyrate.core.Reader import Reader
from pyrate.utils import enums


class ReaderMDETECT(Reader):
    __slots__ = [
        "f",
        "structure",
        "_mmf",
        "_mmmd",
        "azimuth",
        "elevation",
    ]

    def __init__(self, name, config, store, logger, f_name, structure):
        super().__init__(name, config, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):

        # initialise here the data structure used to
        # provide events when the local index is refreshed.

        self.is_loaded = True

        f = open(self.f, "r", encoding="utf-8")
        self._mmf = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
        f.close()

        # md = open(os.path.join(os.path.dirname(self.f), self.structure["metadata"]), "r", encoding="utf-8")
        # self._mmmd = mmap.mmap(md.fileno(), length=0, access=mmap.ACCESS_READ)
        # md.close()

        self.azimuth = float(self.structure["azimuth"])
        self.elevation = float(self.structure["elevation"])

        self._mmf.seek(self._mmf.rfind(b"Coincidenes"))
        n_coincidences = str(self._mmf.readline().decode("utf-8").split(":")[1])
        n_coincidences = int(n_coincidences.replace(" ", ""))

        rate = str(self._mmf.readline().decode("utf-8").split(":")[1])
        rate = float(rate.replace(" ", ""))

        self._mmf.seek(self._mmf.rfind(b"Coincidence cross-reference"))
        line = str(self._mmf.readline().decode("utf-8"))
        line = str(self._mmf.readline().decode("utf-8"))

        print(line)

        sys.exit()

        self._idx = 0

    def offload(self):
        self.is_loaded = False

        self.f.close()

    def read(self, name):

        # if "GROUP:" in name:
        #    pass

        if name.startswith("EVENT:"):

            _, variable = self._break_path(name)

            self._read_variable(name, variable)

        elif name.startswith("INPUT:"):

            self.store.put(name, enums.Pyrate.INVALID_VALUE)

    def set_n_events(self):
        """Retrieves total number of events using the number of events."""
        if not self._n_events:
            self._n_events = self.f[self.structure["datasetname"]].shape[0]

    def _read_variable(self, name, variable):
        """Reads a variable value from the HDF5 and puts it on the transient store."""

        value = enums.Pyrate.INVALID_VALUE

        if variable == "elevation_i":
            value = self.f[self.structure["datasetname"]][self._idx, 2]
            value = float(value)

            if value <= 0.0:
                value = 1e-32

        if variable == "azimuth_i":
            value = self.f[self.structure["datasetname"]][self._idx, 3]
            value = float(value)

            if value <= 0.0:
                value = 1e-32

            # The input true value of the azimuth needs correction.
            value = 360.0 - value

        if variable == "sensors_intensities":
            array = self.f[self.structure["datasetname"]][self._idx, 8:]
            value = pd.DataFrame(
                data=[array], columns=[f"SiPM{idx}" for idx in range(1, 25)]
            )

        if "SiPM" in variable:
            value = self.f[self.structure["datasetname"]][
                self._idx, int(variable.split("SiPM")[1]) + 7
            ]
            value = float(value)

        self.store.put(name, value)

    def _break_path(self, name):
        """This function breaks the name field."""
        return name.split(":")


# EOF
