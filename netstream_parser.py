import bitstring
from time import time


class NetstreamParser:

    def __init__(self, frame_number, netstream):
        self.frame_number = frame_number
        self.netstream = self._reverse_bytewise(netstream)

    def parse_frames(self):  # Lets try to parse one frame successful before this gets looped
        netstream = self.netstream  # because writing fucking self again and again is annoying as shit
        current_time = self._reverse_bytewise(netstream.read('bits:32')).floatle
        delta_time = self._reverse_bytewise(netstream.read('bits:32')).floatle
        print(current_time)
        print(delta_time)

    def _reverse_bytewise(self, bitstream):  # TODO Check if bitstream is multiple of 8 and applay padding
        start = time()
        result = []
        for byte in bitstream.bytes:
            result.append(self._reverse_byte(byte))
        reverse_bytes = bitstring.ConstBitStream(bytes=result)
        delta = time() - start
        print('method three took', delta)
        return reverse_bytes

    def _reverse_byte(self, x):
        x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
        x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
        return x