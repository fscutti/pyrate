""" Output base class. 
"""
import os

from pyrate.core.Writer import Writer
from pyrate.writers.WriterROOT import WriterROOT

from pyrate.utils import functions as FN
from pyrate.utils import strings as ST


class Output(Writer):
    def __init__(self, name, store, logger, iterable=(), **kwargs):
        super().__init__(name, store, logger)
        self.__dict__.update(iterable, **kwargs)

    def load(self):

        self.writers = {}
        targets = []
        for name, attr in self.outputs.items():
            self._init_writer(name, attr["path"], attr["objects"])
            targets.extend(attr["objects"])

        self.set_targets(targets)
    
    def write(self, name):

        for w_name, writer in self.writers.items():
            if name in writer.targets:
                writer.write(name)

    def _init_writer(self, f_name, f_path, w_targets):

        w_name = "_".join([self.name, f_name.split(".", 1)[0]])

        if not w_name in self.writers:

            f = os.path.join(f_path, f_name)

            if f.endswith(".root"):
                writer = WriterROOT(w_name, self.store, self.logger, f, w_targets)
                self.writers[w_name] = writer

            elif f.endswith(".dat"):
                pass

            writer.load()



# EOF
