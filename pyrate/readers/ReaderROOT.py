""" Reader of a ROOT file.
"""
import ROOT as R
import numpy as np

class ReaderROOT:
    __slots__ = ["f","treename","_tree","_nevents","_is_loaded","_idx","istore"]
    def __init__(self, f, treename = None):
        self.f = f
        self.treename = treename
        self._is_loaded = False

    def load(self, istore = None):
        self.f = R.TFile.Open(self.f)
        if istore: self.istore = istore
        if self.treename:
            self._tree = self.f.Get(self.treename)
            self._nevents = self._tree.GetEntries()
            self._idx = 0
            self._tree.GetEntry(self._idx)
        self._is_loaded = True

    def get_next_event(self):
        """ If the next event reading will not be valid it outputs -1.
        """
        
        if self._idx < self._nevents - 1: 
            self._idx += 1
            self._tree.GetEntry(self._idx)
            return self._idx
        else:
            return -1

    def get_idx(self):
        if self._idx:
            return self._idx 
        else: 
            print("ERROR: tree not loaded")

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
   
    def is_loaded(self):
        return self._is_loaded


