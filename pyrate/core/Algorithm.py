""" Algorithm class.
"""

class Algorithm:
    __slots__ = ["name", "_store"]
    def __init__(self, name, store):
        self.name = name
        self._store = store

    def initialise(self, config):
        """ Override this method to define algorithms.
            config is a dictionary. 
        """
        pass
    
    def execute(self, config):
        """ Override this method to define algorithms.
            config is a dictionary. 
        """
        pass
    
    def finalise(self, config):
        """ Override this method to define algorithms.
            config is a dictionary. 
        """
        pass

    def get(self, name, opt="TRAN"):
        """ Retrieves object from the store. Possibly remove this method.
        """
        return self._store.get(name, opt)
    
    def put(self, name, obj, opt="TRAN"):
        """ Puts object on the store. If ready, it sets its status. Possibly remove this method.
        """
        return self._store.put(name, obj, opt)
    
# EOF
