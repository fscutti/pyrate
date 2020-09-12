""" Generic Writer base class.
"""

class Writer:
    __slots__=["name", "store", "targets", "_is_loaded"]
    def __init__(self, name, store):
        self.name = name
        self.store = store
        self.targets = []
    
    def is_loaded(self):
        """ Returns loading status of the Writer
        """
        return self._is_loaded
    
    def is_finished(self):
        """ All objects have been written.
        """
        pass

    def load(self):
        """ Initialises the targets. The file will be opened only when needed.
        """
        pass
    
    def put_object(self, name):
        """ Write object in file. Will open the file if not already open.
        """
        pass
    
# EOF
