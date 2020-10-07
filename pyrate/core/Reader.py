""" Generic Reader base class.
"""


class Reader:
    __slots__ = ["name", "store", "logger", "_idx", "_idx_min", "_idx_max", "_n_events"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        self._idx = 0
        self._idx_min = 0
        self._idx_max = -1
        self._n_events = None

    def load(self):
        """Initialises reader condition members and puts it in a 'read ready' condition."""
        pass

    def read(self, name):
        """Gets object with given name. Event and global variables should be prepended a flag."""
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
        pass

    def set_n_events(self):
        """Computes total number of events."""
        pass

    def set_next_event(self):
        """Updates idx to next event"""
        pass

    def set_previous_event(self):
        """Sets idx to previous event."""
        pass

    def set_split_event(self):
        """Constructs idx conditions to handle event in segments."""
        pass


# EOF
