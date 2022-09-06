""" Output class. 
"""
import os

from pyrate.core.Writer import Writer
from pyrate.writers.WriterROOT import WriterROOT

from pyrate.utils import functions as FN
from pyrate.utils import strings as ST


class Output(Writer):
    def __init__(self, name, config, store, logger, iterable=(), **kwargs):
        super().__init__(name, config, store, logger)
        self.__dict__.update(iterable, **kwargs)

        self._writer = None

    def write(self, name):
        self.writer.write(name)

    @property
    def writer(self):
        return self._writer

    @writer.setter
    def writer(self, file_format):

        if self._writer is None:

            if "root" in file_format:
                self._writer = WriterROOT(
                    self.name,
                    self.config,
                    self.store,
                    self.logger,
                )

            elif ".dat" in file_format:
                pass

    @property
    def targets(self):
        return self.writer.targets

    def load(self):

        # this calls the setter method above.
        self.writer = self.config["format"]

        self.writer.load()

        self.is_loaded = True


# EOF
