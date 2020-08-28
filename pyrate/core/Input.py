""" Base class for reading input files. 
"""

from pyrate.readers.ReaderROOT import ReaderROOT

class Input:
    def __init__(self, name, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.name = name
        self.istore = {}
    
    def load(self):
        self.groups = {"group_{}".format(g):group for g, group in enumerate(self.files)}
        self._nfiles = len(self.groups["group_0"])
        self._f_idx = 0
        self._ev_idx = 0
        self._is_finished = False
        
        for g, files in self.groups.items(): 
            files[self._f_idx] = self._init_reader(files[self._f_idx])
        

    def is_finished(self):
        """ All events have been read at least once.
        """
        return self._is_finished

    def _next_files(self):
        """ Advances the pointer to the next valid group of files
            and initialises a Reader class. This is "transforming"
            a string to a class so it will leave a class instance 
            as a trace of previous usage.
        """
        if self._f_idx < self._nfiles - 1:
            self._f_idx += 1
            for g, files in self.groups.items(): 
                files[self._f_idx] = self._init_reader(files[self._f_idx])

        else: 
            self._f_idx = -1

        return self._f_idx


    def _init_reader(self, f):
        """ Instantiate different readers here.
        """
        reader = None
        if isinstance(f, str):
            if f.endswith(".root"): 
                reader = ReaderROOT(f,self.tree)
            
            elif f.endswith(".dat"): 
                pass
            
            elif f.endswith(".txt"): 
                pass
            
            reader.load()
        
        else: print("ERROR: trying to reinitialise reader")
        return reader

    def get_next_event(self):

        self._ev_idx += 1
        for g, files in self.groups.items(): 
            if files[self._f_idx].get_next_event() < 0:
                if self._next_files() < 0:
                    self._ev_idx = -1
                    return self._ev_idx
        return self._ev_idx



    def get_ev_idx(self):
        if self._ev_idx:
            return self._ev_idx
        else:
            print("ERROR event index not defined")




    def get_previous_event(self):
        pass

    def get_split_event(self):
        pass

    def get_object(self,name):

        pass
