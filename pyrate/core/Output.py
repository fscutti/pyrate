""" Output base class. 
"""
from pyrate.core.Writer import Writer

from pyrate.utils import functions as FN

class Output(Writer):
    def __init__(self, name, store, iterable=(), **kwargs):
        super().__init__(name, store)
        self.__dict__.update(iterable, **kwargs)

    def load(self):
        print(self.__dict__) 
        self.targets = FN.flatten([[o for o in attr["objects"]] for name, attr in self.outputs.items()])



    def _init_writer(self):
        pass
# EOF
