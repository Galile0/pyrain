import bitstring
from time import time
import pprint

BOOL = 'bool'

class NetstreamParser:

    def __init__(self, frame_number, netstream, objects):
        self.frame_number = frame_number
        self.netstream = self._reverse_bytewise(netstream)
        self.objects = objects

    def parse_frames(self):  # Lets try to parse one frame successful before this gets looped
        netstream = self.netstream  # because writing fucking self again and again is annoying as shit
        current_time = self._reverse_bytewise(netstream.read('bits:32')).floatle
        delta_time = self._reverse_bytewise(netstream.read('bits:32')).floatle
        print('CTime %s' % current_time)
        print('DTime %s' % delta_time)
        pprint.pprint(self._parse_actors(netstream))

    def _parse_actors(self, netstream):
        actors = {}
        while True:  # Actor Replicating Loop
            actor = {}
            actor_present = netstream.read(BOOL)
            if not actor_present:
                break
            actor_id = self._reverse_bytewise(netstream.read('bits:10')).uintle
            actor['channel_open'] = netstream.read(BOOL)
            actor['actor_new'] = netstream.read(BOOL)
            if not actor['channel_open'] or not actor['actor_new']:  # Temporary since existing actors are not supported yet
                actors[actor_id] = actor
                break
            actor['actor_data'] = self._parse_new_actor(netstream)
            actor['vector'] = self._read_variable_vector(netstream)
            actors[actor_id] = actor
        return actors

    def _parse_new_actor(self, netstream):
        unknown = netstream.read(BOOL)
        type_id = self._reverse_bytewise(netstream.read('bits:32')).uintle
        type_name = self.objects[type_id]
        return {'Unknown Flag': unknown,
                'type_id': type_id,
                'type_name': type_name}

    def _reverse_bytewise(self, bitstream, dbg=False):
        # start = time()
        result = []
        if dbg: print(bitstream.bin)
        for byte in bitstream.tobytes():
            if dbg: print(hex(byte))
            result.append(self._reverse_byte(byte))
        reverse_bytes = bitstring.ConstBitStream(bytes=result)
        # delta = time() - start
        # print('method three took', delta)
        return reverse_bytes

    def _reverse_byte(self, x):
        x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
        x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
        x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
        return x

    def _read_vector(self, netstream, size):
        length = self._reverse_bytewise(netstream.read(size)).uintle + 2
        x = self._reverse_bytewise(netstream.read(length)).uintle
        y = self._reverse_bytewise(netstream.read(length)).uintle
        z = self._reverse_bytewise(netstream.read(length)).uintle
        return x, y, z

    def _read_serialized_int(self, netstream, max_value=19):
        value = 0
        bits_read = 0

        while True:
            if netstream.read(1).bool:
                value += (1 << bits_read)
            bits_read += 1
            possible_value = value + (1 << bits_read)
            if possible_value > max_value:
                return value

    def _read_variable_vector(self, netstream):
        length = self._read_serialized_int(netstream) + 2
        x = self._reverse_bytewise(netstream.read(length)).uintle
        y = self._reverse_bytewise(netstream.read(length)).uintle
        z = self._reverse_bytewise(netstream.read(length)).uintle
        return (x, y, z)