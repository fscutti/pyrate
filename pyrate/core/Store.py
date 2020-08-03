""" Store class """

def Store:
    def __init__(self):
        self._transient = {}
        self._permanent = {}
    
    def put(self, name, item, mode="TRAN"):
        if mode=="PERM":    self._permanent[name] = item
        elif mode=="TRAN":  self._transient[name] = item
    
    def get(self, name):
        if name in self._transient:   return self._transient[name] 
        elif name in self._permanent: return self._permanent[name] 
        else: print("Some error message")
