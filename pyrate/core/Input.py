""" Base class for reading input files. 
"""

from pyrate.readers.ReaderROOT import ReaderROOT

class Input:
    def __init__(self, name, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.name = name
        self.inputs = {}
    
    def setup(self):
        self.groups = {"group_{}".format(g):group for g, group in enumerate(self.files)}
        for g, files in self.groups.items(): 
            files[0] = self._init(files[0])
        
        print(self.groups)


    def _init(self, f):
        if isinstance(f, str):
            if f.endswith(".root"): 
                return ReaderROOT(f)
        else: print("ERROR: trying to reinitialise reader")


    #def load(self):
    #    pass

    def get_next_event(self):
        pass
    
    def get_previous_event(self):
        pass

    def get_split_event(self):
        pass

    def get_object(self,name):

        pass
