""" Reader of binary files from CAEN1730 digitizers using the raw firmware.
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to the scheme given in the CAEN1730 manual

EVENT or INPUT (header) variables should be accessed using the namespace reported in the following dictionaries:
    Example: EVENT:board_2:raw_waveform_ch_3, EVENT:timestamp, INPUT:n_boards, INPUT:board_1:name, etc...
"""
import os
import mmap
import struct

from pyrate.core.Reader import Reader

class ReaderCAEN1730_RAW(Reader):
    __slots__ = [
        "f",
        "structure",
        "_mmf",
        "_currentEventTimestamp",
        "_currentChannelMask",
        "_currentEventWaveforms",
        "_currentEventChannelRead",
        "_nextEventPos"
    ]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):
        self.is_loaded = True

        self.f = open(self.f, "rb")        
        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self.f.close()

        self._nextEventPos = 0
        #TODO: call this here? what is the order of set_n_events and read?
        self._get_next_event()

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def read(self, name):
        if name.startswith("EVENT:"):            
            #Split the request
            nameSplit = name.split(":")
            board = int(nameSplit[1].split("_")[-1])
            ch = int(nameSplit[2].split("_")[-1])
            variable = nameSplit[-1]
            
            #Get the event value
            if variable=="timestamp":
                value = self._currentEventTimestamp
            elif variable=="waveform":
                value = self._get_waveform(board,ch)
                
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
        while(True):
            #Read in the event info from the header
            #TODO: Do something with all of these values, debugging etc.                    
            head1 = self._mmf.read(4)
            if(head1 == bytes()):
                break

            self._n_events +=1
            head1 = int.from_bytes(head1,"little")
            eventSize = head1 & 0b00001111111111111111111111111111
            self._mmf.seek(4*(eventSize-1),1)

        self._mmf.seek(0, 0)
        
    def _get_next_event(self):
        #Seek to the start of the next event
        self._mmf.seek(self._nextEventPos, 0)

        #Read in the event info from the header
        head1 = self._mmf.read(4)
        head1 = int.from_bytes(head1,"little")
        eventSize = head1 & 0b00001111111111111111111111111111
        
        head2 = self._mmf.read(4)
        head2 = int.from_bytes(head2,"little")
        boardID = head2 & 0b11111000000000000000000000000000
        pattern = head2 & 0b00000000111111111111111100000000
        channelMaskLo = head2 & 0b11111111

        head3 = self._mmf.read(4)
        head3 = int.from_bytes(head3,"little")
        channelMaskHi = head3 & 0b11111111000000000000000000000000
        evtCount = head3 & 0b00000000111111111111111111111111

        head4 = self._mmf.read(4)
        head4 = int.from_bytes(head4,"little")
        TTT = head4

        self._currentEventTimestamp = pattern << 32 + TTT
        self._currentChannelMask = (channelMaskHi << 8) + (channelMaskLo)        

        #Figure out what channels are in the event
        numCh = 0
        self._currentEventChannelRead = {}
        self._currentEventWaveforms = {}        
        for i in range(15):
            if self._currentChannelMask & (1 << i):
                numCh += 1
                self._currentEventChannelRead[i] = False
                self._currentEventWaveforms[i] = []
            
        recordSize = int(2*(eventSize - 4)/numCh)

        #Read in the waveform data
        for i in range(15):
            if self._currentChannelMask & (1 << i):
                for j in range(recordSize):
                    sample = self._mmf.read(2)
                    self._currentEventWaveforms[i].append(int.from_bytes(sample,"little"))

        #Set the start of the new event
        self._nextEventPos = self._mmf.tell()


    def _get_waveform(self, board, ch):
        """Reads variable from the event and puts it in the transient store."""
        #If this channel has already been read assume it's a new event and load the next event
        #TODO: Check that this channel is present in the event first
        #TODO: Make sure the event corresponds to the right board, multiboard not currently implemented        
        if(self._currentEventChannelRead[ch] == True):
            self._get_next_event()

        #Return the waveform and mark that this channel has been read
        self._currentEventChannelRead[ch] = True;
        return self._currentEventWaveforms[ch]

# EOF
