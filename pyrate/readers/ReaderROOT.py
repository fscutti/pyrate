""" Reader of a ROOT file.
"""
import ROOT as R
import numpy as np

class ReaderROOT:
    __slots__ = ["f", "treename"]
    def __init__(self, f, treename = None):
        self.f = f
        self.treename = treename
    
    def load(self, istore = None):
        self.f = R.TFile.Open(self.f)
        if istore: self.istore = istore
        if self.treename:
            self._tree = self.f.Get(self.treename)
            self._nevents = self._tree.GetEntries()
            self.idx = 0

    def get_next_event(self):
        
        if self.idx < self._nevents: 
            self._tree.GetEntry(self._idx)
            self.idx += 1
            return self.idx
        else:
            return -1

    def get_previous_event(self):
        pass

    def get_split_event(self):
        pass

    def get_object(self, name):
        if "hist" in name: self._get_hist(name)
    
    def _get_hist(self, name):
        
        if self.istore[name]: 
            self.istore[name].Add(self.f.Get(name))
        else: 
            self.istore[name] = self.f.Get(name)
   
    


