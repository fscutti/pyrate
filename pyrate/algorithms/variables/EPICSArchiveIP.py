""" Reads SC data from the EPICS Archiver (through ip socket)
    
    Required parameters:
        ip: (str) The ip of the Archiver data retrieval server (including port number)
        epochtime: (int) The epoch time corresponding to the start of the run
        pv: Name of the EPICS process variable to read
    
    Required inputs:
        timestamp: (int_like) The variable to used to timestamp the data
    
    Example config:
    ElapsedTime:
        algorithm: EPICSArchiveIP
        ip: 10.100.13.78:17668
        epochtime: 1644991273
        pv: HILDAQ:elapsedTime
        input:
          timestamp: EVENT:board_0:ch_0:ch_timestamp
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

import urllib3
import json
import datetime
import pytz

class EPICSArchiveIP(Algorithm):
    __slots__ = ("_data","_idx")

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
            if(len(self._data) - self._idx > 1):
                lastTime = self._data[self._idx]['secs']
                nextTime = self._data[self._idx + 1]['secs']
                if(lastTime <= evtTime and nextTime > evtTime):                
                    success = 1
                    value = self._data[self._idx]['val'] #TODO: Interpolate values?
                    break
            
                # If not update the index
                self._idx += 1
            else:
                break

        return (success,value)
    
    def getBuffer(self, startTime):
        # Get 1 hour of data
        startTime = datetime.datetime.utcfromtimestamp(startTime)
        endTime = startTime + datetime.timedelta(days = 1)

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
