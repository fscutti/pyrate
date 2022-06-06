""" Reader of binary files from CAEN1730 digitizers using the zle firmware.
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to the scheme given in the PSD manual
"""
import os
import mmap
import struct
from pyrate.utils.enums import Pyrate
import numpy as np

from pyrate.core.Reader import Reader

class ReaderCAEN1730_PSD(Reader):
    __slots__ = [
        "f",
        "_mmf",
        "_mmfSize",
        "_eventPos",
        "_readIdx",
        "_coincWind",
        "_hasSubEvent",
        "_inSub",
        "_subTime",
        "_subChTimes",
        "_subWaveforms",
        "_inEvt",
        "_evtTime",
        "_evtTimeMax",
        "_evtChTimes",
        "_evtWaveforms",
    ]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name

    def load(self):
        self.is_loaded = True

        self.f = open(self.f, "rb")        
        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self.f.close()

        self._eventPos = []
        self._hasSubEvent = False
        self._mmfSize = self._mmf.size()

        #TODO: Configure thie
        self._coincWind = 1000
        
    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def read(self, name):
        if(self._readIdx != self._idx):
            self._read_event()        
            self._readIdx = self._idx

        if name.startswith("EVENT:"):            
            #Split the request
            path = self._break_path(name)

            #Get the event value
            if path["variable"]=="timestamp":
                value = self._evtTime
            elif path["variable"]=="ch_timestamp":
                value = self._get_timestamps(path["ch"])
            elif path["variable"]=="waveform":
                value = self._get_waveform(path["ch"])
                
            #Add the value to the transiant store
            self.store.put(name, value, "TRAN")
                
        elif name.startswith("INPUT:"):
            pass
        
    def set_n_events(self):
        """Reads number of events using the last event header."""
        #Seek to the start of the file
        self._mmf.seek(0, 0)
        self._n_events = 0

        #Scan through the entire file
        #TODO: This is hard to do without scanning through the entire file.  Skipping through like this will over estimate the number of events.
        #TODO: The idea of a pyrate event is somewhat different from the idea of a digitizer event (especially between instances).  Need to discuss
        while(True):
            #TODO: An alternate which gets the actual number of events.  Not very fast though
            #self._eventPos.append(self._mmf.tell())
            #self._read_event()
            #self._n_events +=1
            #if(self._mmf.tell() == self._mmfSize):
            #    break

            #Read in the event info from the header
            self._eventPos.append(self._mmf.tell())
            head1 = self._mmf.read(4)
            if(head1 == bytes()):
                break

            #If we read something, increment the event counter and skip to the next event
            self._n_events +=1
            head1 = int.from_bytes(head1,"little")
            eventSize = head1 & 0b00001111111111111111111111111111
            
            seekSize = 4*(eventSize - 1) # How far we need to jump
            # Make sure we're not seeking beyond the EOF
            if (self._mmf.tell() + seekSize) > self._mmfSize:
                break
            
            self._mmf.seek(seekSize, 1)

        self._mmf.seek(0, 0)
        self._idx = 0
        self._readIdx = -1

    def _break_path(self, path):
        """Takes a path request from pyrate and splits it into a dictionary"""
        splitPath = path.split(":")

        ret = {}
        ret["variable"] = splitPath[-1]
        if(len(splitPath) > 2):            
            ret["board"] = int(splitPath[1].split("_")[-1])
            if(len(splitPath) > 3):            
                ret["ch"] = int(splitPath[2].split("_")[-1])
        
        return ret

    def _get_waveform(self,  ch):
        """Reads variable from the event and puts it in the transient store."""
        #If the channel is not in the event return an empty list
        #ToDo: Confirm this behaviour in pyrate
        if(ch not in self._inEvt.keys()):
            return Pyrate.NONE

        #Return the waveform and mark that this channel has been read
        return np.array(self._evtWaveforms[ch], dtype='int32')

    def _get_timestamps(self, ch):
        #If the channel is not in the event return an empty list
        #ToDo: Confirm this behaviour in pyrate
        if(ch not in self._inEvt.keys()):
            return Pyrate.NONE

        #Return the waveform and mark that this channel has been read
        return self._evtChTimes

    def _read_event(self):
        #Reset event
        self._evtTime = 2**64
        self._evtTimeMax = 2**64
        self._inEvt = {};
        self._evtChTimes = {};
        self._evtWaveforms = {}
        
        self._AddSubEvent()

        while(True):
            if(self._read_sub_event() == False):
                break
            
            if(self._AddSubEvent() == False):
                break

    def _AddSubEvent(self):
        #Return false if there's no sub event
        if(self._hasSubEvent == False):
            return False;
                
        #Return false if the subevent isn't in the coincidence window
        if(self._subTime > self._evtTime + self._coincWind):        
            return False;        
        
        #Return false if a channel is already present in the event
        for i in range(16):
            if(i in self._inSub.keys() and i in self._inEvt.keys()):
                return False;
                    
        #Otherwise, add the subevent to the event
        if(self._subTime < self._evtTime):        
            self._evtTime = self._subTime
        
        if(self._subTime + self._coincWind > self._evtTimeMax or self._evtTimeMax == 2**64):
            self._evtTimeMax = self._subTime + self._coincWind;
            if(self._evtTimeMax < 0):
                self._evtTimeMax = 2**64
                
        for i in range(16):        
            if(i in self._inSub.keys()):            
                self._inEvt[i] = True;
                self._evtChTimes[i] = self._subChTimes[i];
                self._evtWaveforms[i] = self._subWaveforms[i];                    

        #Reset the subevent             
        self._hasSubEvent = False;
    
    def _read_sub_event(self):
        #self._mmf.seek(self._eventPos[self._idx],0)
        self._hasSubEvent = True
        #Read in the event info from the header
        head1 = self._mmf.read(4)
        if(head1 == bytes()):
            return False
                
        head1 = int.from_bytes(head1,"little")
        head2 = self._mmf.read(4)
        head2 = int.from_bytes(head2,"little")
        head3 = self._mmf.read(4)
        head3 = int.from_bytes(head3,"little")
        head4 = self._mmf.read(4)
        head4 = int.from_bytes(head4,"little")        

        eventSize = head1 & 0b00001111111111111111111111111111
        dualChannelMask =  (head2 & 0b11111111)
        evtCount = head3 & 0b00000000111111111111111111111111

        self._subTime = 2**64
        self._inSub = {};
        self._subChTimes = {};
        self._subWaveforms = {}        
        #Scan through the channel headers
        for i in range(8):
            if(dualChannelMask & (1<<i)):
                chHead1 = self._mmf.read(4)
                chHead1 = int.from_bytes(chHead1,"little")        
                chHead2 = self._mmf.read(4)
                chHead2 = int.from_bytes(chHead2,"little")

                aggregateSize = chHead1 & 0b00000000001111111111111111111111;      
                recordSize = chHead2 & 0b00000000000000001111111111111111;

                chTime = self._mmf.read(4)
                chTime = int.from_bytes(chTime,"little")
                ch = 2*i + ((chTime & 0b10000000000000000000000000000000) >> 31)

                self._subWaveforms[ch] = []
                self._inSub[ch] = True
                recordSize = int(recordSize *8/2)
                for j in range(recordSize):
                    sample = self._mmf.read(4)
                    sample = int.from_bytes(sample,"little")
                    self._subWaveforms[ch].append((sample & 0b00000000000000000011111111111111));
                    self._subWaveforms[ch].append((sample & 0b00111111111111110000000000000000) >> 16);
                    
                extras = self._mmf.read(4);
                extras = int.from_bytes(extras,"little")
                charge = self._mmf.read(4);
                charge = int.from_bytes(charge,"little")

                qLong = (charge & 0b11111111111111110000000000000000) >> 16;
                qShrt = (charge & 0b00000000000000000111111111111111);
                timeHi =  ((extras & 0b11111111111111110000000000000000) << 15)
                timeLo =  (chTime & 0b01111111111111111111111111111111);
                self._subChTimes[ch] = timeHi + timeLo

                if (self._subChTimes[ch] < self._subTime):		
                    self._subTime = self._subChTimes[ch];
		

# EOF
