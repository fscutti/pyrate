""" Generic Reader base class.
"""


class Reader:
    __slots__ = ["name", "store", "logger", "_idx", "_n_events", "_is_loaded"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        # Events are numbered from 0 to n-1.
        self._idx = 0
        self._n_events = None
        # self._is_loaded = False

    # def is_loaded(self):
    #    """ Returns loading status of the Reader.
    #    """
    #    return self._is_loaded

    # def is_finished(self):
    #    """Checks if event pointer is at the end of the input."""
    #    assert (
    #        self._n_events
    #    ), "ERROR: number of events not computed for reader {}".format(self.name)
    #    return self._idx == self._n_events - 1

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
