""" Store class.
"""

from pyrate.utils import functions as FN
from copy import copy

class Store:
    def __init__(self,name,run):
        self.name = name
        self._run = run
        self.objects = {"PERM":{}, "TRAN":{}}
        self.status = {}
        self._state = None
        #self._inputs  = {}
        #self._outputs = {}

    def set_state(self, state):
        self._state = state


    def put(self, name, obj, opt="TRAN"):
        """ Objects should be put on the store only once!
        """
        if FN.has_key(name, self.objects[opt]):
            print("ERROR: objects should only be put on the store once")
            return
        self.objects[opt][name] = obj


    def get(self, name, opt="TRAN"):
        """ try/except method
        """
        try:
            return copy(self.objects[opt][name])
        
        except KeyError:
            self._run.update(name,self,self._state) 
            return copy(self.objects[opt][name])

    def clear(self, opt="TRAN"):
        self.objects[opt] = {}


    def isready(self, name):
        if FN.has_key(name, self.objects["PERM"]) or FN.has_key(name, self.objects["TRAN"]):
            self.status[name] = True
        else:
            print("ERROR message")






