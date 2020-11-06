""" Computation of PMT Baseline.
"""

from pyrate.core.Algorithm import Algorithm


class Baseline(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        #=== CH: 0 EVENTID: 1 FCR: 496 Baseline: 0.000000 V Amplitude: 0.000000 V Charge:    0.000 pC LeadingEdgeTime:  0.000 ns TrailingEdgeTime:  0.000 ns TrigCount: 0 TimeCount 177 ===
        #=== UnixTime = 1571206401.215 date = 2019.10.16 time = 17h.13m.21s.215ms == TDC From FPGA = 39804 == TDC Corrected = 17h13m21s,000.199.020ns === 
        val10 = self.store.get("EVENT:UnixTime")
        #print("EVENT:UnixTime", val10)

        val11 = self.store.get("EVENT:date")
        #print("EVENT:date", val11)
        val12 = self.store.get("EVENT:time")
        val13 = self.store.get("EVENT:TDC From FPGA")
        val13 = self.store.get("EVENT:TDC Corrected")
        #print("EVENT:time", val12)

        val7 = self.store.get("EVENT:CH3:TrigCount")
        val71 = self.store.get("EVENT:CH3:TimeCount")
        val0 = self.store.get("EVENT:CH7:EVENTID")
        val90 = self.store.get("EVENT:CH7:RawWaveform")
        val901 = self.store.get("EVENT:CH3:RawWaveform")
        val2 = self.store.get("EVENT:CH0:Baseline")
        val4 = self.store.get("EVENT:CH3:Charge")
        val3 = self.store.get("EVENT:CH3:Amplitude")
        val14 = self.store.get("EVENT:TDC Corrected")
        val5 = self.store.get("EVENT:CH0:LeadingEdgeTime")
        val1 = self.store.get("EVENT:CH6:FCR")
        #print("Event idx from store:", self.store.get("EVENT:idx"), val90[0])


        head1 = self.store.get("INPUT:DATA SAMPLES")
        #print(head1)
        head2 = self.store.get("INPUT:NB OF CHANNELS ACQUIRED")
        #print(head2)
        head3 = self.store.get("INPUT:Sampling Period")
        #print(head3)
        
        head4 = self.store.get("INPUT:Sampling Period")
        #print(head4)
        
        head5 = self.store.get("INPUT:INL Correction")
        #print(head5)

        """
        print("EVENT:TDC From FPGA", val13)

        
        #print(self.store.get("EVENT:idx"))
        #print("EVENT:CH0:TrailingEdgeTime", val6)
        #print("EVENT:CH0:TrigCount", val7)
        
        val8 = self.store.get("EVENT:CH0:TimeCount")
        #print("EVENT:CH0:TimeCount", val8)
        #summation= 0 
        """
        

        #val9 = self.store.get("EVENT:CH4:RawWaveform")
        """
        print("len(EVENT:CH4:RawWaveform)", len(val9))
        if self.store.get("EVENT:idx") == 39245:
            print(len(val9))
            print(val9[:-1023])
        #if isinstance(val9, list):
        #    print(val9[0],val9[1],val9[2])
        #print("EVENT:CH0:EVENTID", val0)

        """

        """
        #print("EVENT:CH0:FCR", val1)
        #print("EVENT:CH0:Baseline", val2)
        #print("EVENT:CH0:Amplitude", val3)
        #print("EVENT:CH0:Charge", val4)
        #print("EVENT:CH0:LeadingEdgeTime", val5)
        val6 = self.store.get("EVENT:CH0:TrailingEdgeTime")
        """
        """
        print("EVENT:CH7:RawWaveform", val9)
        if self.store.get("EVENT:idx") == 39245:
            print(len(val9))
            print(val9[0])
        #print()
        """

        #print("EVENT:TDC Corrected", val14)
        #self.store.get("EVENT:UnixTime")
        #"""
        pass


# EOF
