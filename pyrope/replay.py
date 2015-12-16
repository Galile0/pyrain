from collections import OrderedDict

import bitstring

from pyrope.header import Header
from pyrope.netstream import Netstream
from pyrope.utils import read_string, UINT_32, FLOAT_LE_32, ParsingError
'''
Assumed File Structure:
4 Bytes size of header starting after CRC
4 Bytes CRC
8 Bytes Version
Header Data introduced by the string TAGame.Replay_Soccar_TA
Netstream Data
Meta Data
'''


class Replay:

    def __init__(self, path):
        self.replay = bitstring.ConstBitStream(filename=path)
        self.header = None
        self.netstream_raw = None
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

    def parse(self, parse_header=True, parse_netstream=False):
        self.replay.pos = 0  # Just reassure we are at the beginning
        header_size = self.replay.read(UINT_32)  # Read header size and discard
        self.crc = self.replay.read('hex:32')
        self.version = str(self.replay.read(UINT_32)) + '.' + str(self.replay.read(UINT_32))
        self.header = Header(self.replay.read((header_size-8)*8))
        self.replay.read('bytes:8')  # Read and discard additional size info
        self.maps = self._decode_maps(self.replay)
        self.keyframes = self._decode_keyframes(self.replay)
        self.netstream = Netstream(self.replay.read(self.replay.read(UINT_32)*8))
        self.dbg_log = self._decode_dbg_log(self.replay)
        self.goal_frames = self._decode_goalframes(self.replay)
        self.packages = self._decode_packages(self.replay)
        self.objects = self._decode_objects(self.replay)
        self.names = self._decode_names(self.replay)
        self.class_index_map = self._decode_class_index_map(self.replay)
        self.netcache = self._decode_class_net_cache(self.replay, self.class_index_map)
        if self.replay.bytepos != (self.replay.length/8):
            raise ParsingError("Did not reach EOF while gathering Meta Data")
        if parse_header or parse_netstream:  # Netstream needs header for frame amount
            self.header.parse()
        if parse_netstream:
            self.netstream.parse_frames(self.header.parsed['NumFrames'], self.objects, self.netcache)
        return True

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
            next_cache_index = index+1
            while True:  # iterate until we found a cache with our parent id
                nextitem = list(cachelist[next_cache_index].values())[0]
                if nextitem['cache_id'] == list(item.values())[0]['parent']:
                    nextitem.update(item)  # Parent found, add our element to it
                    break  # On to the next cache
                else:
                    next_cache_index += 1
        return cachelist[-1]

    def get_pos_vector(self):
        if self.netstream.frames:
            self.netstream.get_pos()
        else:
            raise AttributeError("Frames not yet parsed")

    def get_actor_list(self):
        if self.netstream.frames:
            return self.netstream.get_actor_list()
        else:
            raise AttributeError("Frames not yet parsed")

    def get_player(self): # Todo add check that frames are actually parsed
        player = {}
        for frame in self.netstream.frames.values():
            for name, value in frame.actors.items():
                if "e_Default__PRI_TA" in name:
                    try:
                        player[value['data']['Engine.PlayerReplicationInfo:PlayerName']] = value['actor_id']
                    except: pass
        return player

    def player_to_car_ids(self, playerid):
        result = []
        for frame in self.netstream.frames.values():
            for actor in frame.actors.values():
                try:
                    if "Engine.Pawn:PlayerReplicationInfo" in actor['data']:
                        if actor['actor_id'] not in result and actor['data']["Engine.Pawn:PlayerReplicationInfo"][1]==playerid:
                            result.append(actor['actor_id'])
                except: pass
        return result

    def get_player_pos(self, playerid):
        cars = self.player_to_car_ids(playerid)
        car_data = OrderedDict()
        for car in cars:
            car_data[car] = {'pos': [], 'destr': 'None'}
        for num, frame in self.netstream.frames.items():
            for actor in frame.actors.values():
                if actor['actor_id'] in cars: # Found an Actor that is in our wanted list
                    if str(actor['actor_id'])+'d' in frame.actors: # We found a destroyed actor, lets investigate
                        if 'd_Ball_Default' in frame.actors: # Ball got destroyed, only reason -> goal
                            car_data[actor['actor_id']]['destr'] = 'goal'
                        else: # Other reason is car exploded
                            car_data[actor['actor_id']]['destr'] = 'demolish'
                    try:
                        pos = actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos']
                        car_data[actor['actor_id']]['pos'].append(pos)
                    except: pass
        result = []
        for k,v in car_data.items():
            if not result:  # We need some kind of root
                result.append(v['pos'])
                continue
            if v['destr'] == 'demolish':
                result[-1].extend(v['pos'])  # merge pos data since car just respawned normally
            else:
                result.append(v['pos'])  # Car got reset because of goal, make new position set
        return result

    def get_ball_pos(self):
        result = {'x': [], 'y': [], 'z': []}
        for num, frame in self.netstream.frames.items():
            for actor in frame.actors.values():
                if "Ball_Default" in actor['actor_type']:
                    try:
                        result['x'].append(actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos'][0])
                        result['y'].append(actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos'][1])
                        result['z'].append(actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos'][2])
                    except: pass
        return result