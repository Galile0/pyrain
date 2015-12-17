import json
from collections import OrderedDict

from pyrope.frame import Frame, FrameParsingError
from pyrope.netstream_property_mapping import PropertyMapper
from pyrope.utils import reverse_bytewise
import sys

'''
Serialization Structure for Frame as follows:
{
 FrameID: {
           CurrentTime: Float,
           DeltaTime: Float,
           Actors: {
                    Shortname: {
                                actorId: Int,
                                actor_type: FullType,
                                new: boolean,
                                open: boolean,
                                startpos: int,
                                data: Array[{property_name: property_value}]
                                }
                    }
           }
}
'''


class NetstreamParsingError(Exception):
    pass


class Netstream:
    def __init__(self, netstream):
        self._netstream = reverse_bytewise(netstream)
        self.frames = OrderedDict()
        self._toolbar_width = 50

    def parse_frames(self, framenum, objects, netcache):
        self.frames = {}

        sys.stdout.write("[%s]" % (" " * self._toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self._toolbar_width+1))
        update_bar_each = framenum//self._toolbar_width

        propertymapper = PropertyMapper(netcache)
        for i in range(framenum):
            frame = Frame()
            try:
                frame.parse_frame(self._netstream, objects, propertymapper)
            except FrameParsingError as e:
                e.args += ({"LastFrameActors": self.frames[i-1].actors},)
                raise e
            self.frames[i] = frame

            if i % update_bar_each == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
        sys.stdout.write("\n")
        remaining = self._netstream.read(self._netstream.length-self._netstream.pos)
        remaining.bytealign()
        if remaining.int != 0:
            raise NetstreamParsingError("There seems to be meaningful data left in the Netstream", remaining.hex)
        return self.frames

    def to_json(self, skip_empty=True):
        def nonempty(framedict):
            frames = OrderedDict()
            for k, v in framedict:
                if v.actors:
                    frames[k] = v.__dict__
            return frames
        if skip_empty:
            return json.dumps(self, default=lambda o: nonempty(self.frames.items()), indent=2)
        return json.dumps(self, default=lambda o: {k: v.__dict__ for k, v in self.frames.items()}, indent=2)
