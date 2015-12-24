import json
from collections import OrderedDict

import bitstring

from pyrope.netstream_property_mapping import PropertyMapper
from pyrope.utils import read_string, UINT_32, UINT_64, FLOAT_LE_32, ParsingError, reverse_bytewise
from pyrope.frame import Frame, FrameParsingError
'''
Assumed File Structure:
4 Bytes size of header starting after CRC
4 Bytes CRC
8 Bytes Version
Header Data introduced by the string TAGame.Replay_Soccar_TA
Netstream Data
Meta Data
'''


class NetstreamParsingError(Exception):
    pass


class HeaderParsingError(Exception):
    pass


class Replay:
    def __init__(self, path=None):
        self._header_raw = None
        self.header = None
        self._netstream_raw = None
        self.netstream = None
        self.crc = None
        self.version = None
        self.maps = None
        self.keyframes = None
        self.dbg_log = None
        self.goal_frames = None
        self.packages = None
        self.objects = None
        self.names = None
        self.class_index_map = None
        self.netcache = None
        if path:
            self._replay = bitstring.ConstBitStream(filename=path)
            self._parse_meta()
            self._parse_header()

    def parse_netstream(self, qout=None, ev=None):
        try:
            self._netstream_raw = reverse_bytewise(self._netstream_raw)
            self.netstream = self._parse_frames(qout, ev)
        except Exception as e:
            if qout:
                qout.put('exception')
                qout.put(e)

    def _parse_meta(self):
        self._replay.pos = 0  # Just reassure we are at the beginning
        header_size = self._replay.read(UINT_32)  # Read header size and discard
        self.crc = self._replay.read('hex:32')
        self.version = str(self._replay.read(UINT_32)) + '.' + str(self._replay.read(UINT_32))
        self._header_raw = self._replay.read((header_size - 8) * 8)
        self._replay.read('bytes:8')  # Read and discard additional size info
        self.maps = self._decode_maps(self._replay)
        self.keyframes = self._decode_keyframes(self._replay)
        self._netstream_raw = self._replay.read(self._replay.read(UINT_32) * 8)
        self.dbg_log = self._decode_dbg_log(self._replay)
        self.goal_frames = self._decode_goalframes(self._replay)
        self.packages = self._decode_packages(self._replay)
        self.objects = self._decode_objects(self._replay)
        self.names = self._decode_names(self._replay)
        self.class_index_map = self._decode_class_index_map(self._replay)
        self.netcache = self._decode_class_net_cache(self._replay, self.class_index_map)
        if self._replay.bytepos != (self._replay.length / 8):
            raise ParsingError("Replay not compatible. "
                               "Did not reach EOF while gathering Meta Data")
        return True

    def _parse_header(self):
        read_string(self._header_raw)  # Read and discard TAGame.Replay_Soccar_TA
        self.header = self._decode_properties(self._header_raw)

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
        entries = {}
        for i in range(entrie_number):
            entries[i] = read_string(bitstream)
        return entries

    def _decode_names(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = []
        for i in range(entrie_number):
            entries.append(read_string(bitstream))
        return entries

    def _decode_class_index_map(self, bitstream):
        entrie_number = bitstream.read(UINT_32)
        entries = {}
        for i in range(entrie_number):  # corresponds to object table
            name = read_string(bitstream)
            class_id = bitstream.read(UINT_32)
            entries[class_id] = name
        return entries

    def _decode_class_net_cache(self, bitstream, class_index_map):
        entrie_number = bitstream.read(UINT_32)
        cachelist = []
        for i in range(entrie_number):
            class_id = bitstream.read(UINT_32)  # relates to id in class_index_map
            parent = bitstream.read(UINT_32)
            cache_id = bitstream.read(UINT_32)
            length = bitstream.read(UINT_32)
            mapping = {}
            for j in range(length):
                property_index = bitstream.read(UINT_32)
                property_mapped_index = bitstream.read(UINT_32)
                mapping[property_mapped_index] = property_index
            data = {
                'mapping': mapping,
                'parent': parent,
                'cache_id': cache_id
            }
            cachelist.append({class_index_map[class_id]: data})
        cachelist.reverse()  # Build netcache tree by "furling" our netcaches from behind
        for index, item in enumerate(cachelist[:-1]):  # Worst case should be O(n^2)
            next_cache_index = index + 1
            while True:  # iterate until we found a cache with our parent id
                nextitem = list(cachelist[next_cache_index].values())[0]
                if nextitem['cache_id'] == list(item.values())[0]['parent']:
                    nextitem.update(item)  # Parent found, add our element to it
                    break  # On to the next cache
                else:
                    next_cache_index += 1
        return cachelist[-1]

    def _decode_properties(self, bitstream):
        properties = {}
        while True:
            name, value = self._decode_property(bitstream)
            if name:
                properties[name] = value
            else:
                return properties

    def _decode_property(self, bitstream):
        property_key = read_string(bitstream)
        if property_key == 'None':
            return None, None
        property_type = read_string(bitstream)
        property_value_size = bitstream.read(UINT_64)
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
            raise HeaderParsingError("Unknown property type %s for %s" % (property_type, property_key))
        return property_key, property_value

    def _parse_frames(self, qout, ev_stop):
        frames = OrderedDict()
        propertymapper = PropertyMapper(self.netcache)
        for i in range(self.header['NumFrames']):
            if ev_stop and ev_stop.is_set():
                self._netstream_raw.pos = 0  # Reset in case parsing gets restarted
                qout.put('abort')
                return None
            frame = Frame()
            try:
                frame.parse_frame(self._netstream_raw, self.objects, propertymapper)
            except FrameParsingError as e:
                e.args += ({"LastFrameActors": frames[i-1].actors},)
                raise e
            frames[i] = frame
            if qout:
                qout.put(i)
        remaining = self._netstream_raw.read(self._netstream_raw.length - self._netstream_raw.pos)
        remaining.bytealign()
        if remaining.int != 0:
            raise NetstreamParsingError("There seems to be meaningful data left in the Netstream", remaining.hex)
        qout.put('done')
        return frames

    def __getstate__(self):
        d = dict(self.__dict__)
        if '_replay' in d:
            del d['_replay']
        if '_netstream' in d:
            del d['_netstream_raw']
        if '_header' in d:
            del d['_header_raw']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)

    def netstream_to_json(self, skip_empty=True):
        def nonempty(framedict):
            frames = OrderedDict()
            for k, v in framedict:
                if v.actors:
                    frames[k] = v.__dict__
            return frames
        if skip_empty:
            return json.dumps(self, default=lambda o: nonempty(self.netstream.items()), indent=2)
        return json.dumps(self, default=lambda o: {k: v.__dict__ for k, v in self.netstream.items()}, indent=2)

    def metadata_to_json(self):
        d = OrderedDict([('CRC', self.crc),
                        ('Version', self.version),
                        ('Header', self.header),
                        ('Maps', self.maps),
                        ('KeyFrames', self.keyframes),
                        ('Debug Log', self.dbg_log),
                        ('Goal Frames', self.goal_frames),
                        ('Packages', self.packages),
                        ('Objects', self.objects),
                        ('Names', self.names),
                        ('Class Map', self.class_index_map),
                        ('Netcache Tree', self.netcache)])
        return json.dumps(d, indent=2)
