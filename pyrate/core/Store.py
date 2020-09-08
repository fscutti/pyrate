""" Store class.
"""

class Store:
    def __init__(self,name,run):
        self.name = name
        self._run = run
        self.objects = {"PERM":{}, "TRAN":{}, "READY":{}}
        # PERM: objects which are persistent throughout the run.
        # TRAN: objects which are volatile and removed after each input/event loop.
        # READY: map holding the boolean status of objects which are ready for the finalise step.

    def check(self, name, opt="TRAN"):
        """ Checks if object is in the store.
        """
        return name in self.objects[opt]

    def put(self, name, obj, opt="TRAN", force=False):
        """ Objects should be put on the store only once!
        """
        
        # Maybe this check can be removed but just to be careful for now...
        if self.check(name, opt) and not force:
            print("ERROR: objects should only be put on the store once")
            return
        
        self.objects[opt][name] = obj
        
    def get(self, name, opt="TRAN"):
        """ try/except method
        """
        try:
            return self.objects[opt][name]
        
        except KeyError:

            self._run.update(name,self) 
            return self.objects[opt][name]

    def clear(self, opt="TRAN"):
        self.objects[opt] = {}
    
# EOF
