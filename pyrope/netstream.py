from pyrope.frame import Frame, FrameParsingError
from pyrope.netstream_property_mapping import PropertyMapper
from pyrope.utils import reverse_bytewise
import sys


class NetstreamParsingError(Exception):
    pass


class Netstream:
    def __init__(self, netstream):
        self._netstream = reverse_bytewise(netstream)
        self.frames = None
        self._toolbar_width = 50

    def parse_frames(self, framenum, objects, netcache):
        self.frames = []

        sys.stdout.write("[%s]" % (" " * self._toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self._toolbar_width+1))
        update_bar_each = framenum//self._toolbar_width

        propertymapper = PropertyMapper(netcache)
        for i in range(framenum):
            frame = Frame(i)
            try:
                frame.parse_frame(self._netstream, objects, propertymapper)
            except FrameParsingError as e:
                e.args += ({"LastFrameActors": self.frames[i-1].actors},)
                raise e
            self.frames.append(frame)

            if i % update_bar_each == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
        sys.stdout.write("\n")
        remaining = self._netstream.read(self._netstream.length-self._netstream.pos)
        remaining.bytealign()
        if remaining.int != 0:
            raise NetstreamParsingError("There seems to be meaningful data left in the Netstream", remaining.hex)
        return self.frames

    def get_movement(self, actor=None):
        if actor:
            pass
        else:
            pass

    def get_actor_list(self):
        return self.frames[0].actor_appeared
