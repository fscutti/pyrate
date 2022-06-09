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
    def writer(self, config):

        if self._writer is None:

            if self.name.endswith(".root"):
                self._writer = WriterROOT(
                    self.name,
                    config,
                    self.store,
                    self.logger,
                )

            elif self.name.endswith(".dat"):
                pass

    def load(self):

        self.writer = self.config
        self.is_loaded = True


# EOF
