from netstream_parser import NetstreamParser
from utils import read_string, UINT_32, UINT_64, FLOAT_LE_32
import bitstring
from collections import OrderedDict

'''
Assumed File Structure:
4 Bytes size of header starting after CRC
4 Bytes CRC
8 Bytes Version
Header Data introduced by the string TAGame.Replay_Soccar_TA
Netstream Data
'''


class ReplayParser:

    def __init__(self, replay_file):
        self.replay = bitstring.ConstBitStream(filename=replay_file)

    def parse_file(self):
        parsed_replay = OrderedDict()
        self.replay.read('bytes:4')  # Read header size and discard
        parsed_replay['crc'] = self.replay.read('hex:32')
        parsed_replay['version'] = str(self.replay.read(UINT_32)) + '.' + str(self.replay.read(UINT_32))
        read_string(self.replay)  # Read and discard TAGame.Replay_Soccar_TA
        parsed_replay['header'] = self._decode_properties(self.replay)
        self.replay.read('bytes:8')  # Read and discard additional size info
        parsed_replay['maps'] = self._decode_maps(self.replay)
        parsed_replay['keyframes'] = self._decode_keyframes(self.replay)
        parsed_replay['netstream_size'] = self.replay.read(UINT_32)
        netstream = self.replay.read(parsed_replay['netstream_size']*8)
        NetstreamParser(parsed_replay['netstream_size'], netstream).parse_frames()
        parsed_replay['netstream_data'] = netstream.hex
        parsed_replay['dbg_log'] = self._decode_dbg_log(self.replay)
        parsed_replay['goal_frames'] = self._decode_goalframes(self.replay)
        parsed_replay['packages'] = self._decode_packages(self.replay)
        parsed_replay['objects'] = self._decode_objects(self.replay)
        parsed_replay['names'] = self._decode_names(self.replay)
        parsed_replay['class_index_map'] = self._decode_class_index_map(self.replay)
        parsed_replay['class_net_cache'] = self._decode_class_net_cache(self.replay)
        if self.replay.bytepos == (self.replay.length/8):
            print("Reached end of File as expected. Parsing successful")
        else:
            print("Shit has hit the fan, parsing did not reach eof")
        return parsed_replay

    def _decode_properties(self, bitstream):
        properties = {}
        while True:
            property = self._decode_property(bitstream)
            if property:
                properties[property['key']] = property['value']
            else:
                return properties

    def _decode_property(self, bitstream):
        property_key = read_string(bitstream)
        if property_key == 'None':
            return None
        property_type = read_string(bitstream)
        property_value_size = bitstream.read(UINT_64)
        property_value = None
        if property_type == 'IntProperty':
            property_value = bitstream.read(UINT_32)
        elif property_type == 'StrProperty':
            property_value = read_string(bitstream)
        elif property_type == 'FloatProperty':
            property_value = bitstream.read(FLOAT_LE_32)
        elif property_type == 'NameProperty':
            property_value = read_string(bitstream)
        elif property_type == 'ArrayProperty':
            array_length = bitstream.read(UINT_32)
            property_value = [
                self._decode_properties(bitstream)
                for i in range(array_length)
            ]
        elif property_type == 'ByteProperty':
            key_text = read_string(bitstream)
            value_text = read_string(bitstream)
            property_value = {key_text: value_text}
        elif property_type == 'QWordProperty':
            property_value = bitstream.read(64).uint
        elif property_type == 'BoolProperty':
            property_value = bitstream.read(8).uint == 1
        else:
            print("Unknown property type '{}' for {}".format(property_type, property_key))
        return {'key': property_key, 'value': property_value}

    def _decode_maps(self, bitstream):
        maps = []
        array_len = bitstream.read(UINT_32)
        for i in range(array_len):
            maps.append(read_string(bitstream))
        return maps

    def _decode_keyframes(self, bitstream):
        keyframe_num = bitstream.read(UINT_32)
        keyframes = []
        for i in range(keyframe_num):
            keyframes.append({'time': bitstream.read(FLOAT_LE_32),
                              'frame': bitstream.read(UINT_32),
                              'position': bitstream.read(UINT_32)})
        return keyframes

    def _decode_dbg_log(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):
            entries.append({'frame': bitstream.read(UINT_32),
                        'player': read_string(bitstream),
                        'data:': read_string(bitstream)})
        return entries

    def _decode_goalframes(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):
            entries.append({'type': read_string(bitstream),
                        'frame': bitstream.read(UINT_32)})
        return entries

    def _decode_packages(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):
            entries.append(read_string(bitstream))
        return entries

    def _decode_objects(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):
            entries.append(read_string(bitstream))
        return entries

    def _decode_names(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):
            entries.append(read_string(bitstream))
        return entries

    def _decode_class_index_map(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):  # corresponds to object table
            entries.append({'name': read_string(bitstream),
                            'id': bitstream.read(UINT_32)})
        return entries

    def _decode_class_net_cache(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = {}
        for i in range(entrie_number):
            class_id = bitstream.read(UINT_32)  # relates to id in class_index_map
            index_start = bitstream.read(UINT_32)
            index_end = bitstream.read(UINT_32)
            length = bitstream.read(UINT_32)
            data = {'index_start': index_start,
                    'index_end': index_end}
            mapping = {}
            for j in range(length):
                property_index = bitstream.read(UINT_32)
                property_mapped_index = bitstream.read(UINT_32)
                mapping[property_index] = property_mapped_index
            data['mapping'] = mapping
            entries[class_id] = data
        return entries