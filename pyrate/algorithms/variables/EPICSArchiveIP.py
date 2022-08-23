""" Calculates the mean, stddev, skew and excess kurtosis of a waveform,
    treating the waveform as a over the passed in window range.
    The moments heavily depend on the window passed in. For best results, ensure
    that your windows are tuned for your expected pulse lengths.
    Momrnt = sum(x_i - mu)^n/N / stddev^n

    
    Required parameters:
        rate: (float) The digitisation rate
    
    Required inputs:
        waveform: (array-like) A waveform-like object
        window: (tuple-like) A window object

    Optional parameters:
        mode: (str) Let's the user change to algebraic moments instead of
                    central, normalised moments. To get the algebraic moments
                    pass in the flag "algebraic"
    

    Example config:
    
    Skew_CHX:
        algorithm: Moment
        rate: 500e6
        input:
            waveform: CorrectedWaveform_CHX
            window: Window_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

import urllib3
import json
import datetime
import pytz

class EPICSArchiveIP(Algorithm):
    __slots__ = ("_ip", "_pv", "_startTime","_data","_idx")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        # Get the first buffer from the input epoch time
        self.getBuffer(self.config["epochtime"])        

    def execute(self, condition=None):
        # Get the event timestamp from the store
        evtTime = self.store.get(self.config["input"]["timestamp"])
        if evtTime == Pyrate.NONE:
            return        
        evtTime = 8*evtTime/1000000000.0 + self.config["epochtime"]
        
        # Get the value from the current buffer
        (success,value) = self.getValue(evtTime)
        if(success == 1):
            self.store.put(self.name, value)

    def getValue(self, evtTime):
        success = 0
        value = Pyrate.NONE
        while(True):
            # If there's no data in the buffer, get a new one
            if(self._idx >= len(self._data) - 2):
                self.getBuffer(self._data[self._idx]['secs'])
                # TODO: Check for a valid response
                            
            # If the last event comes before our event and the next event comes after we're in the right spot and can break
            if(self._data[self._idx]['secs'] < evtTime and self._data[self._idx + 1]['secs'] > evtTime):
                success = 1
                value = self._data[self._idx]['val'] #TODO: Interpolate values?
                break
            
            # If not update the index
            self._idx += 1

        return (success,value)
    
    def getBuffer(self, startTime):
        # Get 1 hour of data
        startTime = datetime.datetime.fromtimestamp(startTime - 10*60*60)
        endTime = startTime + datetime.timedelta(hours = 1)

        # Convert start/end times into strings
        pvStr = self.config['pv'].replace(":","%3A")
        startStr = startTime.strftime("%Y-%m-%dT%H:%M:%S").replace(":","%3A")
        endStr = endTime.strftime("%Y-%m-%dT%H:%M:%S").replace(":","%3A")

        # Send the request to the archiver server
        string = f"http://{self.config['ip']}/retrieval/data/getData.json?pv={pvStr}&from={startStr}.000Z&to={endStr}.000Z"
        http = urllib3.PoolManager()
        req = http.request('GET',string)
        # Decode the response
        # TODO: Check for a valid response
        if(req.status == 200):
            data = req.data.decode("utf-8")
            data = json.loads(data)            
            self._data = data[0]['data']
            self._idx = 0

# EOF
