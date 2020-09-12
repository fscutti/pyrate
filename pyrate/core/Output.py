""" Output base class. 
"""
import os

from pyrate.core.Writer import Writer

from pyrate.utils import functions as FN

class Output(Writer):
    def __init__(self, name, store, iterable=(), **kwargs):
        super().__init__(name, store)
        self.__dict__.update(iterable, **kwargs)

    def load(self):
        
        for name, attr in self.outputs.items():
            f_name = os.path.join(name, attr["path"])
            self._init_writer(f_name, attr["objects"])
            self.targets.extend(attr["objects"])


    def _init_writer(self, f_name, w_targets):
        pass
# EOF
