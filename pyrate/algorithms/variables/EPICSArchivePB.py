""" Reads PB data from the EPICS Archiver
    
    Required parameters:
        dir: (str) The directory where the PB files are located (arch directory)
        epochtime: (int) The epoch time corresponding to the start of the run
        pv: Name of the EPICS process variable to read
    
    Required inputs:
        timestamp: (int_like) The variable to used to timestamp the data
    
    Example config:
    ElapsedTime:
        algorithm: EPICSArchivePB
        dir: /home/msmg/data/arch
        epochtime: 1644991273        
        pv: HILDAQ:elapsedTime
        input:
          timestamp: EVENT:board_0:ch_0:ch_timestamp
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate
from pyrate.utils import EPICSEvent_pb2

import copy
import datetime
import glob
import os

class EPICSArchivePB(Algorithm):
    __slots__ = ("_headers","_currentFile","_lastLine","_nextLine")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self._currentFile = None
        self._headers = EPICSEvent_pb2.PayloadInfo()
        self._lastLine = EPICSEvent_pb2.ScalarInt()
        self._nextLine = EPICSEvent_pb2.ScalarInt()

    def unEscape(self,sample):
        sample = sample.replace(b'\x1b\x03',b'\x0d')
        sample = sample.replace(b'\x1b\x02',b'\x0a')
        sample = sample.replace(b'\x1b\x01',b'\x1b')
        return sample
    
    def initialise(self, condition=None):
        """"""
        self.getBuffer(self.config["epochtime"])
        temp=self.unEscape(self._currentFile.readline().strip())
        self._headers.ParseFromString(temp)
        temp=self.unEscape(self._currentFile.readline().strip())
        self._lastLine.ParseFromString(temp)
        temp=self.unEscape(self._currentFile.readline().strip())
        self._nextLine.ParseFromString(temp)

    def execute(self, condition=None):
        """Takes an event time and finds the relevent line in the csv file"""
        # Get the timestamp from the store and convert to a datetime object
        evtTime = self.store.get(self.config["input"]["timestamp"])
        if (evtTime is Pyrate.NONE):
            return

        evtTime = 8*evtTime/1000000000.0 + self.config["epochtime"]# TODO: These time stamps should probably have a standardised unit
        # Get the value from the current buffer
        success = self.getValue(evtTime)
        if(success == 1):
            self.store.put(self.name,self._lastLine.val)
        
    def getValue(self, evtTime):
        success = 0;
        evtTime = datetime.datetime.utcfromtimestamp(evtTime)
        # Scan through the file until we find the relevant line
        while(True):
            # If we don't have a next line, open the next file
            if(not self._nextLine):
                print("eob")
                #TODO: Get the next file
                break
                
            # If the last line comes before our event and the next line comes after we're in the right spot and can break
            lastTime = datetime.datetime.strptime(str(self._headers.year),"%Y") + datetime.timedelta(seconds = self._lastLine.secondsintoyear, microseconds = self._lastLine.nano/1000.0)
            nextTime = datetime.datetime.strptime(str(self._headers.year),"%Y") + datetime.timedelta(seconds = self._nextLine.secondsintoyear, microseconds = self._nextLine.nano/1000.0)
            if(lastTime <= evtTime and nextTime > evtTime):
                success = 1
                break

            # If not, get the next line and continue
            self._lastLine = copy.deepcopy(self._nextLine)
            temp = self._currentFile.readline()
            if(temp):
                temp=temp.strip()
                temp=self.unEscape(temp)
                try:
                    self._nextLine.ParseFromString(temp)
                except:
                    pass        
        return success
    
    def getBuffer(self,startTime):
        # Get all files in the directory and sort by time
        startTime = datetime.datetime.utcfromtimestamp(startTime)
        pvStr = "/".join(self.config["pv"].split(":"))
        files = glob.glob(f"{self.config['dir']}/lts/**/{pvStr}*.pb",recursive=True)
        files.sort()
        
        # Find/open the file that corresponds to our timestamp
        for i in range(len(files)):
            time1 = files[i].split(":")[1]
            time1 = datetime.datetime.strptime(time1[0:-3],"%Y")
            if(True):
                if(self._currentFile):
                    self._currentFile.close()                    
                self._currentFile = open(files[i],"rb")
                break
# EOF
