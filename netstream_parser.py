import bitstring
from time import time
import pprint

BOOL = 'bool'
BV_SIZE = 4   # how many bits represent the component length of ball position vectors
CV_SIZE = 10  # Same as BV_Size but for Cars respectively
DV_SIZE = 5   # Default value for non car non ball types
'''
NOTES ON VECTOR CODING:
    According to ZoRMonkeys findings the Car Position Vector consists of 10 Bits for component length, which for frame 0
     results in 12 bit Component Size
    According to JJBOts Gihubcode (read_variable_vector) the Car vector for frame 0 has 4 bits for length resulting in
     14 bit component size

    At this point it is unsure which parsing is correct, but the result of 10 bit for length seem more logical compared
    to the ball vector (One Axis identical = Lined up with ball, one axis slightly offset, maybe due to mid air spawn,
    one axis drastical offset, car in front of goal)

    unil further parsing results in clearer data both methods are left in, and can simply be used interchangeable
'''
class NetstreamParser:

    def __init__(self, frame_number, netstream, objects):
        self.frame_number = frame_number
        if netstream: self.netstream = self._reverse_bytewise(netstream)
        if objects: self.objects = objects

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
            actor['start_pos'] = netstream.pos
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
            actors[actor_id] = actor
        return actors

    def _parse_new_actor(self, netstream):
        actor = {}
        actor['unknown_flag'] = netstream.read(BOOL)
        actor['type_id'] = self._reverse_bytewise(netstream.read('bits:32')).uintle
        actor['type_name'] = self.objects[actor['type_id']]
        if 'TheWorld' in actor['type_name']:  # World types are Vector Less
            return actor
        if 'Ball_Default' in actor['type_name']:
            # print("case 1", actor['type_name'])
            actor['vector'] = self._read_pos_vector(netstream, BV_SIZE)
            actor['rotation'] = self._read_rot_vector(netstream)
        elif 'Car_Default' in actor['type_name']:
            # print("case 2", actor['type_name'])
            actor['vector'] = self._read_variable_vector(netstream)  # TODO Refer TO HEADERNOTE
            # actor['vector'] = self._read_pos_vector(netstream, CV_SIZE, False)
            actor['rotation'] = self._read_rot_vector(netstream)

        else:
            # print("case 3", actor['type_name'])
            actor['vector'] = self._read_pos_vector(netstream)
        return actor

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

    def _read_serialized_int(self, netstream, max_value=19):
        value = 0
        bits_read = 0

        while True:
            # print(value, end=' ')
            if netstream.read(1).bool:
                value += (1 << bits_read)
            # print(value, end=' ')
            bits_read += 1
            # print(bits_read, end=' ')
            possible_value = value + (1 << bits_read)
            # print(possible_value)
            if possible_value > max_value:
                # print("length", value)
                return value

    def _read_variable_vector(self, netstream):
        # pos_start = netstream.pos
        length = self._read_serialized_int(netstream) + 2
        # l_bits = netstream.pos - pos_start
        # print("Length %d coded in %d bits" % (length, l_bits))

        x = self._reverse_bytewise(netstream.read(length)).uintle
        y = self._reverse_bytewise(netstream.read(length)).uintle
        z = self._reverse_bytewise(netstream.read(length)).uintle
        # netstream.pos = pos
        return (x, y, z)

    def _read_pos_vector(self, netstream, size=DV_SIZE, add=True):
        # start = netstream.pos
        length = self._reverse_bytewise(netstream.read(size)).uintle
        if add: length += 2
        x = self._reverse_bytewise(netstream.read(length)).uintle
        y = self._reverse_bytewise(netstream.read(length)).uintle
        z = self._reverse_bytewise(netstream.read(length)).uintle
        # delta = netstream.pos - start
        # netstream.pos=start
        # print("RAW: %s" % netstream.read(delta).bin)
        # print("Len: %d" % length)
        # print("Vec: %d %d %d" % (x,y,z))
        # print("=======")
        return x, y, z

    def _read_rot_vector(self, netstream):
        x = y = z = 0
        if netstream.read(BOOL):
            x = self._reverse_byte(netstream.read('uint:8'))
        if netstream.read(BOOL):
            y = self._reverse_byte(netstream.read('uint:8'))
        if netstream.read(BOOL):
            z = self._reverse_byte(netstream.read('uint:8'))
        return x, y, z

if __name__=='__main__':
    v1 = bitstring.ConstBitStream('0b0011000000000000010')
    v2 = bitstring.ConstBitStream('0x601017b')
    p = NetstreamParser(0,None,None)
    r1 = p._read_variable_vector(v1)
    r2 = p._read_pos_vector(v2)
    print(r1)
    print(r2)