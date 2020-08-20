""" Store class.
"""
import sys
import importlib

class Store:
    def __init__(self,name,run):
        self.name = name
        self.run  = None
        self.objects   = {}
        #self._inputs  = {}
        #self._outputs = {}
    
    def get(self, name):
        """ try/except method
        """
        try:
            return self.objects[name]
        except:
            self.run.call(name,self) 
            return self.objects[name]









