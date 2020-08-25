""" Algorithm class.
"""

class Algorithm:
    __slots__ = ["name", "_store"]
    def __init__(self, name, store):
        self.name = name
        self._store = _store

    def initialise(self, config = None, dep = None):
        """ Override this method to define algorithms.
            config is a dictionary. 
        """
        pass
    
    def execute(self, config = None, dep = None):
        """ Override this method to define algorithms.
            config is a dictionary. 
        """
        pass
    
    def finalise(self, config = None, dep = None):
        """ Override this method to define algorithms.
            config is a dictionary. 
        """
        pass

    def get(self, name):
        return self._store.get(name)
    
    def put(self, name, obj):
        return self._store.put(name, obj)
    
    def isready(self, name):
        return self._store.isready(name)
    

# EOF
