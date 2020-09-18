""" Reader of a ROOT file.
"""
import ROOT as R
import numpy as np

from pyrate.utils import functions as FN
from pyrate.core.Reader import Reader

class ReaderROOT(Reader):
    __slots__ = ["f","treename","_tree"]
    def __init__(self, name, store, f, treename = None):
        super().__init__(name, store)
        self.f = f
        self.treename = treename

    def load(self):
        self.f = R.TFile.Open(self.f)
        if self.treename:
            self._tree = self.f.Get(self.treename)
            self._idx = 0
            self._tree.GetEntry(self._idx)
        self._is_loaded = True
        self.get_n_events()
    

    def next_event(self):
        """ If the next event reading will not be valid it outputs -1.
        """
        
        if self._idx < self._n_events - 1: 
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
    
    
    def get_n_events(self):
        if self._n_events:
            return self._n_events 
        else: 
            assert self._tree, "ERROR: tree not loaded for reader {}".format(self.name)
            self._n_events = self._tree.GetEntries()


    def read(self, name):
        if "PMT1_charge_waveform_" in name: self._get_hist(name)
        elif "energy" in name: self._get_waveform(name)
   

    def _get_hist(self, name):
        """ Grabs histograms from the input file and puts them on the permanent store.
        """
         
        h = self.f.Get(name)

        if h: 
            if not self.store.check(name, "PERM"):
                print("This is after the check")
                self.store.put(name,h, "PERM")
                print("The hist is put on the store")
            else:
                print("Trying to update the histogram")
                self.store.get(name, "PERM").Add(h)
                print("Histogram is updated")
            

    def _get_waveform(self, name):
         
        energy = self._tree.edepScint

        self.store.put(name,energy,"TRAN")
