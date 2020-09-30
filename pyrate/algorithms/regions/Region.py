""" Standard Region algorithm.
"""

from pyrate.core.Algorithm import Algorithm


class Region(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        triggerTime = self.store.get("EVENT:SmallMuon:EventData:TriggerTime")
        ch0RawWaveform = self.store.get("EVENT:SmallMuon:Channel_0:RawWaveform")
        startTime = self.store.get("EVENT:RunMetadata:StartTime")
        self.logger.info(
            f"This is the start time: {startTime} from {self.name} for {config['name']}"
        )


# EOF
