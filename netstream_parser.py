from collections import OrderedDict

from network_property_parsing import read_property_value
from utils import read_serialized_int, read_serialized_vector, read_byte_vector, reverse_bytewise, BOOL, ParsingException
import pprint


class NetstreamParser:
    def __init__(self, frame_number, netstream, objects, propertymapper):
        self.frame_number = frame_number
        if netstream:
            self.netstream = reverse_bytewise(netstream)
        if objects:
            self.objects = objects
        if propertymapper:
            self.propertymapper = propertymapper
        self.actor_type = {}  # Mapping of existing actor ids to their type

    def parse_frames(self):  # Lets try to parse one frame successful before this gets looped
        netstream = self.netstream  # because writing fucking self again and again is annoying as shit
        frames = []
        for i in range(self.frame_number):
            current_time = reverse_bytewise(netstream.read('bits:32')).floatle
            delta_time = reverse_bytewise(netstream.read('bits:32')).floatle
            try:
                frames.append({'frame': str(i),
                               'time_now': current_time,
                               'time_delta': delta_time,
                               'data': self._parse_actors(netstream)})
            except ParsingException as e:
                print("DONT KNOW WHAT TO DO! PANIC! ABORT! FLEE YOU FOOLS!")
                pprint.pprint(e.args)
                return frames
        return frames
        # pprint.pprint(self._parse_actors(netstream))

    def _parse_actors(self, netstream):
        actors = []
        while True:  # Actor Replicating Loop
            startpos = netstream.pos
            actor_present = netstream.read(BOOL)

            if not actor_present:
                break
            actorid = reverse_bytewise(netstream.read('bits:10')).uintle
            channel = netstream.read(BOOL)
            if not channel:  # TODO Temporary since existing actors are not supported yet
                try:
                    del self.actor_type[actorid]  # Delete from active actor list
                except KeyError:
                    raise ParsingException("KeyError on Actor delete, this is what i got so far", actors)
                continue

            new = netstream.read(BOOL)
            if new:
                try:
                    data = self._parse_new_actor(netstream)
                except ParsingException as e:
                    print(e)
                    raise ParsingException(actors)
                self.actor_type[actorid] = data['type_name']  # Add actor to currently exist.
            else:
                try:
                    data = self._parse_existing_actor(netstream, self.actor_type[actorid])
                except ParsingException as e:
                    print(e)
                    actors.append(OrderedDict([  # OrderedDict only for readability of json file
                        ('startpos', startpos),
                        ('actor_type', self.actor_type[actorid]),
                        ('actor_id', actorid),
                        ('open', channel),
                        ('new', new)]))
                    raise ParsingException(actors)
                except KeyError as e:
                    print(e)
                    actors.append(OrderedDict([  # OrderedDict only for readability of json file
                        ('startpos', startpos),
                        ('actor_type', 'KeyError'),
                        ('actor_id', actorid),
                        ('open', channel),
                        ('new', new)]))
                    raise ParsingException(actors)
            actors.append(OrderedDict([  # OrderedDict only for readability of json file
                ('startpos', startpos),
                ('actor_type', self.actor_type[actorid]),
                ('actor_id', actorid),
                ('open', channel),
                ('new', new),
                ('data', data)
            ]))
        return actors

    def _parse_existing_actor(self, netstream, actor_type):
        properties = []
        while netstream.read(BOOL):
            property_id = read_serialized_int(netstream, self.propertymapper.get_property_max_id(actor_type))
            property_name = self.objects[self.propertymapper.get_property_name(actor_type, property_id)]
            try:
                property_value = read_property_value(property_name, netstream)
            except ParsingException as e:
                print(e)
                properties.append(OrderedDict([
                    ('property_id', property_id),
                    ('property_name', property_name)
                ]))
                raise ParsingException(properties)
            result = OrderedDict()  # TODO Ordereddict only for debugging
            result['property_id'] = property_id
            result['property_name'] = property_name
            result['property_value'] = property_value
            properties.append(result)
            # properties.append({'property_id': property_id,
            #                    'property_name': property_name,
            #                    'property_value': property_value})
        return properties

    def _parse_new_actor(self, netstream):
        actor = {}
        actor['unknown_flag'] = netstream.read(BOOL)
        actor['type_id'] = reverse_bytewise(netstream.read('bits:32')).uintle
        try:
            actor['type_name'] = self.objects[actor['type_id']]
        except KeyError:
            raise ParsingException("Actor Type ID Not in Objects %d" % actor['type_id'])
        if 'TheWorld' in actor['type_name']:  # World types are Vector Less
            return actor
        actor['vector'] = read_serialized_vector(netstream)
        if 'Ball_Default' in actor['type_name'] or 'Car_Default' in actor['type_name']:
            actor['rotation'] = read_byte_vector(netstream)
        return actor
