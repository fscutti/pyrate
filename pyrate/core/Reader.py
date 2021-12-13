""" Generic Reader base class.
"""


class Reader:
    __slots__ = ["name", "store", "logger", "is_loaded", "_idx", "_n_events"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        self.is_loaded = False
        self._idx = 0
        self._n_events = None

    def load(self):
        """Initialises reader condition members and puts it in a 'read ready' condition."""
        pass

    def offload(self):
        """Closes files."""
        pass

    def read(self, name):
        """Gets object with given name. Event and global variables should be prepended a flag."""

        if "GROUP:" in name:
            pass

        if name.startswith("EVENT:"):
            pass

        elif name.startswith("INPUT:"):
            pass

    def get_idx(self):
        """Gets index of current event. """
        return self._idx

    def get_n_events(self):
        """Returns total number of events."""
        if self._n_events:
            return self._n_events
        else:
            self.set_n_events()
            return self._n_events

    def set_idx(self, idx):
        """Updates idx to defined value"""
        if not self._n_events:
            self.set_n_events()

        if idx > self._n_events - 1:
            self._idx = -math.inf
        else:
            self._idx = idx

    def set_n_events(self):
        """Computes total number of events."""
        pass

    def set_next_event(self):
        """If the next event reading will not be valid it outputs -1."""
        self.set_idx(self._idx + 1)
        return self._idx

    def set_previous_event(self):
        """Sets idx to previous event."""
        pass

    def set_split_event(self):
        """Constructs idx conditions to handle event in segments."""
        pass

    def break_path(self, path):
        """Takes a path request from pyrate and splits it into a dictionary"""
        splitPath = path.split(":")

        ret = {}
        ret["variable"] = splitPath[-1]
        if(len(splitPath) > 2):            
            ret["board"] = int(splitPath[1].split("_")[-1])
            if(len(splitPath) > 3):            
                ret["ch"] = int(splitPath[2].split("_")[-1])
        
        return ret
# EOF
