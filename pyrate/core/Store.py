""" Store class.
"""

from pyrate.utils import functions as FN
from copy import copy

class Store:
    def __init__(self,name,run):
        self.name = name
        self._run = run
        self.objects = {"PERM":{}, "TRAN":{}, "STATUS":{}}
        self._state = None
        #self._inputs  = {}
        #self._outputs = {}

    def set_state(self, state):
        """ Passes to the Store the state of the run.
        """
        self._state = state

    def put(self, name, obj, opt="TRAN", is_ready=False):
        """ Objects should be put on the store only once!
        """

        if FN.has_key(name, self.objects[opt]):
            print("ERROR: objects should only be put on the store once")
            return
        
        self.objects[opt][name] = obj
        
        if is_ready:
            self.objects["STATUS"][name] = True


    def get(self, name, opt="TRAN"):
        """ try/except method
        """
        try:

            return copy(self.objects[opt][name])
        
        except KeyError:

            if not opt=="STATUS":
                self._run.update(name,self,self._state) 
                return copy(self.objects[opt][name])

            else: 
                return False
    
    def clear(self, opt="TRAN"):
        self.objects[opt] = {}


# EOF
