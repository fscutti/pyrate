""" Generic Reader base class.
"""

class Reader:
    __slots__=["name", "store", "_idx", "_n_events", "_is_loaded"]
    def __init__(self, name, store):
        self.name = name
        self.store = store
        self._idx = 0 
        self._n_events = None
        self._is_loaded = False
    
    #def is_loaded(self):
    #    """ Returns loading status of the Reader.
    #    """
    #    return self._is_loaded
    
    def is_finished(self):
        """ Checks if event pointer is at the end of the input.
        """
        assert self._n_events, "ERROR: number of events not computed for reader {}".format(self.name)
        return self._idx == self._n_events - 1 

    def load(self):
        """ Initialises members and puts the reader in a state where something can 
            already be read from some file (implies opening at least some files).
        """
        pass
    
    def read(self, name):
        """ Gets object with given name. 
        Depending on the input format/configuration the name might be remapped to some other string.
        """
        pass
    
    def get_n_events(self):
        """ Computes or returns total number of events.
        """
        pass
    
    def get_idx(self):
        """ Gets index of current event. Events are numbered from 0 to n-1.
        """
        pass
   
    def get_event(self, idx):
        """ Jumps to specific event index.
        """
        pass

    def next_event(self):
        """ Move to next valid event. If next event will not be valid it should return -1, 
        otherwise it returns the current event index.
        """
        pass

    def previous_event(self):
        """ Move to previous valid event. 
        """
        pass
    
    def split_event(self):
        """ Setup conditions to handle the event in segments at any call of next event.
        """
        pass

# EOF
