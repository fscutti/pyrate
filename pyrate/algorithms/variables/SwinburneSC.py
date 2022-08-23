""" Reads csv data from the Swinburne Slow control prototype.
    
    Required parameters:
        dir: (str) The directory where the csv files are located
        epochtime: (int) The epoch time corresponding to the start of the run
    
    Required inputs:
        timestamp: (int_like) The variable to used to timestamp the data
    

    Example config:
    cRIO_RTD_1:
        algorithm: SwinburneSC
        dir: /home/msmg/data/spartan/ostanley/slow_control/
        epochtime: 1644991273
        input:
          timestamp: EVENT:board_0:ch_0:ch_timestamp
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

import datetime
import glob
import os

class SwinburneSC(Algorithm):
    __slots__ = ("_headers","_currentFile","_lastLine","_nextLine")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self._currentFile = None

    @property
    def output(self):
        """Getter method for output objects."""
        return self._output

    @output.setter
    def output(self, config_output):
        """Setter method for output objects."""
        self._output = {
            'Pressure':'Pressure',
            'Humidity':'Humidity',
            'cRIO_RTD_1':'cRIO_RTD_1',
            'cRIO_RTD_2':'cRIO_RTD_2',
            'cRIO_RTD_3':'cRIO_RTD_3',
            'cRIO_RTD_4':'cRIO_RTD_4',
            'Remote_RTD1':'Remote_RTD1',
            'Remote_RTD2':'Remote_RTD2',
            'Remote_RTD3':'Remote_RTD3',
            'Remote_RTD4':'Remote_RTD4',
            'L1_Volts':'L1_Volts',
            'L1_W':'L1_W',
            'L1_VA':'L1_VA',
            'L1_Hz':'L1_Hz',
            'HVPS_CH1_Status':'HVPS_CH1_Status',
            'HVPS_CH2_Status':'HVPS_CH2_Status',
            'HVPS_CH3_Status':'HVPS_CH3_Status',
            'HVPS_CH4_Status':'HVPS_CH4_Status',
            'HVPS_CH1_Volts':'HVPS_CH1_Volts',
            'HVPS_CH2_Volts':'HVPS_CH2_Volts',
            'HVPS_CH3_Volts':'HVPS_CH3_Volts',
            'HVPS_CH4_Volts':'HVPS_CH4_Volts',
            'HVPS_CH1_Current':'HVPS_CH1_Current',
            'HVPS_CH2_Current':'HVPS_CH2_Current',
            'HVPS_CH3_Current':'HVPS_CH3_Current',
            'HVPS_CH4_Current':'HVPS_CH4_Current'}
        
    def initialise(self, condition=None):
        """"""
        startTime = datetime.datetime.fromtimestamp(self.config["epochtime"])
        self.getBuffer(startTime)
        # TODO: Check for a valid file
        # Read the headers and first 2 lines from the file and we're good to go
        self._headers = self._currentFile.readline().split(",")
        self._lastLine = self._currentFile.readline().split(",")
        self._nextLine = self._currentFile.readline().split(",")
    
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
            for i in range(1,len(self._headers)):                
                self.store.put(self._headers[i].replace(" ","_"),float(self._lastLine[i]))

    def finalise(self, condition=None):
        self._currentFile.close()

    def getValue(self, evtTime):
        success = 0;
        evtTime = datetime.datetime.fromtimestamp(evtTime)
        # Scan through the file until we find the relevant line
        while(True):
            # If we don't have a next line, open the next file
            if(not self._nextLine):
                #print(evtTime, self._lastLine)
                self.getBuffer(evtTime)
                self._headers = self._currentFile.readline().split(",")
                self._nextLine = self._currentFile.readline().split(",")
                
            # If the last line comes before our event and the next line comes after we're in the right spot and can break
            lastTime = datetime.datetime.strptime(self._lastLine[0],"%Y-%m-%d %H:%M:%S.%f")
            nextTime = datetime.datetime.strptime(self._nextLine[0],"%Y-%m-%d %H:%M:%S.%f")
            if(lastTime <= evtTime and nextTime > evtTime):
                success = 1
                break

            # If not, get the next line and continue
            self._lastLine = self._nextLine
            self._nextLine = self._currentFile.readline()
            if(self._nextLine):
                self._nextLine = self._nextLine.split(",")
        return success
    
    def getBuffer(self,startTime):
        # Get all files in the directory and sort by time
        files = glob.glob(self.config["dir"]+"/*Slow.csv")
        files.sort()
        
        # Find/open the file that corresponds to our timestamp
        for i in range(len(files) - 1):
            time1 = files[i].split("/")[-1].split("-Slow")[0]
            time2 = files[i + 1].split("/")[-1].split("-Slow")[0]
            time1 = datetime.datetime.strptime(time1,"%Y-%m-%d %H_%M_%S")
            time2 = datetime.datetime.strptime(time2,"%Y-%m-%d %H_%M_%S")
            print(time1,startTime,time2)
            if(time1 <= startTime and time2 > startTime):
                if(self._currentFile):
                    self._currentFile.close()
                    
                self._currentFile = open(files[i],"r")
                #TODO: check for open file
                break

# EOF
