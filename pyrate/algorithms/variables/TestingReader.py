""" Testing a Reader.
"""
import sys
from copy import copy

from pyrate.core.Algorithm import Algorithm


class TestingReader(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        if config["algorithm"]["format"] == "WC":
            # WaveCatcher input:
            # if self.store.get("EVENT:idx") == 0:
            #    DATA_SAMPLES = self.store.get("INPUT:DATA SAMPLES")
            #    NB_OF_CHANNELS_ACQUIRED = self.store.get(
            #        "INPUT:NB OF CHANNELS ACQUIRED"
            #    )
            #    Sampling_Period = self.store.get("INPUT:Sampling Period")
            #    Sampling_Period = self.store.get("INPUT:Sampling Period")
            #    INL_Correction = self.store.get("INPUT:INL Correction")

            # === UnixTime = 1571206401.215 date = 2019.10.16 time = 17h.13m.21s.215ms == TDC From FPGA = 39804 == TDC Corrected = 17h13m21s,000.199.020ns ===
            UnixTime = self.store.get("EVENT:UnixTime")
            date = self.store.get("EVENT:date")
            time = self.store.get("EVENT:time")
            TDC_From_FPGA = self.store.get("EVENT:TDC From FPGA")
            TDC_Corrected = self.store.get("EVENT:TDC Corrected")

            # === CH: 0 EVENTID: 1 FCR: 496 Baseline: 0.000000 V Amplitude: 0.000000 V Charge:    0.000 pC LeadingEdgeTime:  0.000 ns TrailingEdgeTime:  0.000 ns TrigCount: 0 TimeCount 177 ===
            EVENTID = self.store.get("EVENT:CH8:EVENTID")
            FCR = self.store.get("EVENT:CH9:FCR")
            Baseline = self.store.get("EVENT:CH8:Baseline")
            Amplitude = self.store.get("EVENT:CH9:Amplitude")
            Charge = self.store.get("EVENT:CH8:Charge")
            LeadingEdgeTime = self.store.get("EVENT:CH8:LeadingEdgeTime")
            TrailingEdgeTime = self.store.get("EVENT:CH9:TrailingEdgeTime")
            TrigCount = self.store.get("EVENT:CH8:TrigCount")
            TimeCount = self.store.get("EVENT:CH9:TimeCount")
            RawWaveform = self.store.get("EVENT:CH9:RawWaveform")

        elif config["algorithm"]["format"] == "WD":

            # WaveDump input:
            # if self.store.get("EVENT:idx") == 0:
            #    Reading_at = self.store.get("INPUT:Reading at")
            #    Trg_Rate = self.store.get("INPUT:Trg Rate")
            #    Run_Start = self.store.get("INPUT:Run Start")
            #    Run_End = self.store.get("INPUT:Run End")

            # Record Length: 128
            # BoardID:  0
            # Channel: 0
            # Event Number: 45973
            # Pattern: 0x0000
            # Trigger Time Stamp: 3222448449
            # DC offset (DAC): 0x1999

            if self.store.get("EVENT:idx") == 0:
                Reading_at = self.store.get("INPUT:Reading at")
                Trg_Rate = self.store.get("INPUT:Trg Rate")
                Run_Start = self.store.get("INPUT:Run Start")
                Run_End = self.store.get("INPUT:Run End")

            Trigger_Time_Stamp = self.store.get("EVENT:GROUP:wave0:Trigger Time Stamp")
            Trigger_Time_Stamp = self.store.get("EVENT:GROUP:wave1:Trigger Time Stamp")
            Trigger_Time_Stamp = self.store.get("EVENT:GROUP:wave2:Trigger Time Stamp")

            Pattern = self.store.get("EVENT:GROUP:wave0:Pattern")
            Pattern = self.store.get("EVENT:GROUP:wave1:Pattern")
            Pattern = self.store.get("EVENT:GROUP:wave2:Pattern")

            DC_offset_DAC = self.store.get("EVENT:GROUP:wave0:DC offset (DAC)")
            DC_offset_DAC = self.store.get("EVENT:GROUP:wave1:DC offset (DAC)")
            DC_offset_DAC = self.store.get("EVENT:GROUP:wave2:DC offset (DAC)")

            Record_Length = self.store.get("EVENT:GROUP:wave0:Record Length")
            Record_Length = self.store.get("EVENT:GROUP:wave1:Record Length")
            Record_Length = self.store.get("EVENT:GROUP:wave2:Record Length")

            BoardID = self.store.get("EVENT:GROUP:wave0:BoardID")
            BoardID = self.store.get("EVENT:GROUP:wave1:BoardID")
            BoardID = self.store.get("EVENT:GROUP:wave2:BoardID")

            Channel = self.store.get("EVENT:GROUP:wave0:Channel")
            Channel = self.store.get("EVENT:GROUP:wave1:Channel")
            Channel = self.store.get("EVENT:GROUP:wave2:Channel")

            RawWaveform = self.store.get("EVENT:GROUP:wave0:RawWaveform")
            RawWaveform = self.store.get("EVENT:GROUP:wave1:RawWaveform")
            RawWaveform = self.store.get("EVENT:GROUP:wave2:RawWaveform")

            """
            elif config["algorithm"]["format"] == "WD":
            
                # WaveDump input:
                #if self.store.get("EVENT:idx") == 0:
                #    Reading_at = self.store.get("INPUT:Reading at")
                #    Trg_Rate = self.store.get("INPUT:Trg Rate")
                #    Run_Start = self.store.get("INPUT:Run Start")
                #    Run_End = self.store.get("INPUT:Run End")
            
                # Record Length: 128
                # BoardID:  0
                # Channel: 0
                # Event Number: 45973
                # Pattern: 0x0000
                # Trigger Time Stamp: 3222448449
                # DC offset (DAC): 0x1999
            
                Trigger_Time_Stamp = self.store.get("EVENT:Trigger Time Stamp")
            
                Pattern = self.store.get("EVENT:Pattern")
            
                DC_offset_DAC = self.store.get("EVENT:DC offset (DAC)")
            
                Record_Length = self.store.get("EVENT:Record Length")
            
                BoardID = self.store.get("EVENT:BoardID")
            
                Channel = self.store.get("EVENT:Channel")
            
                RawWaveform = self.store.get("EVENT:RawWaveform")
            """

        elif config["algorithm"]["format"] == "ROOT":
            # ROOT input:
            # if self.store.get("EVENT:idx") == 0:
            #    self.store.get("EVENT:GROUP:ch0:RunMetadata:StartTime")
            #    self.store.get("EVENT:GROUP:ch0:RunMetadata:StopTime")
            #
            #    self.store.get("EVENT:GROUP:ch1:RunMetadata:StartTime")
            #    self.store.get("EVENT:GROUP:ch1:RunMetadata:StopTime")
            #
            #    self.store.get("EVENT:GROUP:ch2:RunMetadata:StartTime")
            #    self.store.get("EVENT:GROUP:ch2:RunMetadata:StopTime")

            #self.store.get("EVENT:GROUP:ch0:SmallMuon:EventData:TriggerTime")
            #self.store.get("EVENT:GROUP:ch0:SmallMuon:EventData:TriggeredChannels")

            # self.store.get("EVENT:GROUP:ch1:SmallMuon:EventData:TriggerTime")
            # self.store.get("EVENT:GROUP:ch1:SmallMuon:EventData:TriggeredChannels")

            # self.store.get("EVENT:GROUP:ch2:SmallMuon:EventData:TriggerTime")
            # self.store.get("EVENT:GROUP:ch2:SmallMuon:EventData:TriggeredChannels")

            #w = self.store.get("EVENT:GROUP:ch0:SmallMuon:Channel_0:RawWaveform")
            # print(w.at(0))
            #self.store.get("EVENT:GROUP:ch0:SmallMuon:Channel_0:Baseline")
            # idx = self.store.get("EVENT:idx")
            # self.store.put(f"{idx}", copy(w), "PERM")

            # self.store.get("EVENT:GROUP:ch1:SmallMuon:Channel_0:RawWaveform")
            # self.store.get("EVENT:GROUP:ch1:SmallMuon:Channel_0:Baseline")

            # self.store.get("EVENT:GROUP:ch2:SmallMuon:Channel_0:RawWaveform")
            # self.store.get("EVENT:GROUP:ch2:SmallMuon:Channel_0:Baseline")

            e = self.store.get("EVENT:nT:edepScint")
            print(self.store.get("INPUT:name"))



        elif config["algorithm"]["format"] == "pgSQL":
            # var1 = self.store.get("INPUT:QUERY:SELECT eventrate FROM muonmonitoring ORDER BY time DESC LIMIT 3")
            # print(var1)
            var2 = self.store.get("EVENT:QUERY:muonmonitoring:4:eventrate")
            print(var2)
        
        
        
        elif config["algorithm"]["format"] == "BlueTongue":
            # var1 = self.store.get("INPUT:QUERY:SELECT eventrate FROM muonmonitoring ORDER BY time DESC LIMIT 3")
            # print(var1)
            #var2 = self.store.get("EVENT:QUERY:muonmonitoring:4:eventrate")
            #print(self.store.get("EVENT:idx"))
            
            #self.store.get("EVENT:board_1:raw_waveform_ch_10")
            #self.store.get("EVENT:board_1:time_count_ch_8")
            #self.store.get("EVENT:board_1:trigger_count_ch_10")
            #self.store.get("EVENT:timestamp")
            #print(self.store.get("EVENT:board_1:event_counter"))
            
            """
            print(self.store.get("INPUT:board_1:n_channels"))
            print(self.store.get("INPUT:n_boards"))
            print(self.store.get("INPUT:board_1:name"))
            print(self.store.get("INPUT:board_1:type"))
            print(self.store.get("INPUT:board_1:record_length"))
            print(self.store.get("INPUT:board_1:channel_numbers"))
            """
            pass



































# EOF
