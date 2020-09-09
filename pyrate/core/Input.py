""" Base class for reading input files. 
"""
from pyrate.readers.ReaderROOT import ReaderROOT
from pyrate.utils import functions as FN
from pyrate.utils import strings as ST

class Input:
    #def __init__(self, name, store):
    def __init__(self, name, store, iterable=(), **kwargs):
        self.name = name
        self.store = store
        self.__dict__.update(iterable, **kwargs)
    
    def load(self):

        self._f_idx = 0
        self._ev_idx = 0
        self._is_finished = False
        
        
        print("Name of input: ", self.name)
        print("attributes: ", self.__dict__)
        #print("Input files: ", self.files)
        
        g_names = {0:"0"} 
        if hasattr(self, 'group'):
            for g_idx, g_name in enumerate(ST.get_items(self.group)):
                g_names[g_idx] = g_name

        self.groups = {}
        for g_idx, g_files in enumerate(self.files):
            self.groups[g_names[g_idx]] = g_files
            self._init_reader(g_names[g_idx], self._f_idx, self.store)
        
        self._nfiles = len(g_files)
        

    def is_finished(self):
        """ All events have been read at least once.
        """
        return self._is_finished

    def _move_readers(self, option = "frw"):
        """ Advances the pointer to the next valid group of files
            and initialises a Reader class. This is "transforming"
            a string to a class so it will leave a class instance 
            as a trace of previous usage.
        """

        if option == "frw":

            if self._f_idx < self._nfiles - 1:
                self._f_idx += 1
                
                for g_name in self.groups:
                    self._init_reader(g_name, self._f_idx, self.store)
            
            else: 
                self._f_idx = -1
            
            return self._f_idx

        elif option == "bkw":
            """
            if self._f_idx > 0:
                self._f_idx -= 1
                
                for g_name in self.groups:
                    self._init_reader(g_name, self._f_idx, self.store)
            
            else: 
                self._f_idx = -1
            
            return self._f_idx
            """
            pass



    def _init_reader(self, g_name, f_idx, store):
        """ Instantiate different readers here. If the instance exists nothing is done.
            This function transforms a string into a reader.
        """
        r_name = "_".join([g_name,str(f_idx)])

        if isinstance(self.groups[g_name][f_idx],str):

            f = self.groups[g_name][f_idx]

            if f.endswith(".root"): 
               reader = ReaderROOT(r_name,f,self.tree,store)
            
            elif f.endswith(".dat"): 
                pass
            
            elif f.endswith(".txt"): 
                pass
        
            reader.load()
        
            self.groups[g_name][f_idx] = reader




    def get_next_event(self):
        """ Move to the next event in the sequence.
        """
        for g_name, g_readers in self.groups.items():

            if g_readers[self._f_idx].get_next_event() < 0:
                if self._move_readers("frw") < 0:

                    self._ev_idx = -1
                    return self._ev_idx

                else: 
                    self._ev_idx += 1
                    return self._ev_idx

        self._ev_idx += 1
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
        
        """ Look for the object in the entire input. Initialises readers if they were not.
            Only one group should be sufficient to retrieve the object. Exceptions should
            be treated at the input and not at the readers level.
            
        """
        
        n_tags = name.split("_")

        for g_name, g_readers in self.groups.items():
            
            if len(self.groups)>1:
                if not ST.check_tag(g_name, n_tags):
                    continue

            self._init_reader(g_name, self._f_idx, self.store)
            
            g_readers[self._f_idx].get_object(name)

      



