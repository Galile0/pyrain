from network_property_parsing import read_property_value
from utils import read_serialized_int, read_pos_vector, read_rot_vector, reverse_bytewise, BOOL, ParsingException
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
        self.actor_type = {}  # Mapping actor id to their type for reference by existing actors

    def parse_frames(self):  # Lets try to parse one frame successful before this gets looped
        netstream = self.netstream  # because writing fucking self again and again is annoying as shit
        current_time = reverse_bytewise(netstream.read('bits:32')).floatle
        delta_time = reverse_bytewise(netstream.read('bits:32')).floatle
        print('CTime %s' % current_time)
        print('DTime %s' % delta_time)
        pprint.pprint(self._parse_actors(netstream))

    def _parse_actors(self, netstream):
        actors = []
        while True:  # Actor Replicating Loop
            actor = {}
            actor['start_pos'] = netstream.pos
            actor_present = netstream.read(BOOL)
            if not actor_present:
                break

            actor['actor_id'] = reverse_bytewise(netstream.read('bits:10')).uintle
            actor['channel_open'] = netstream.read(BOOL)
            if not actor['channel_open']:  # Temporary since existing actors are not supported yet
                # self.actors[actor_id] = actor
                break

            actor['actor_new'] = netstream.read(BOOL)
            if actor['actor_new']:
                actor['actor_data'] = self._parse_new_actor(netstream)
                self.actor_type[actor['actor_id']] = actor['actor_data']['type_name']
            else:
                actor['actor_data'] = self._parse_existing_actor(netstream, self.actor_type[actor['actor_id']])
                actors.append(actor)
                break  # TODO REmove break when existing actor parsing is completed
            actors.append(actor)
        return actors

    def _parse_existing_actor(self, netstream, actor_type):
        properties = []
        while netstream.read(BOOL):
            property_id = read_serialized_int(netstream, 36)
            property_name = self.objects[self.propertymapper.get_property_name(actor_type, property_id)]
            try:
                property_value = read_property_value(property_name, netstream)
            except ParsingException as e:
                print(e)
                break
            properties.append({'property_id': property_id,
                               'property_name': property_name,
                               'property_value': property_value})
        return {'properties': properties}

    def _parse_new_actor(self, netstream):
        actor = {}
        actor['unknown_flag'] = netstream.read(BOOL)
        actor['type_id'] = reverse_bytewise(netstream.read('bits:32')).uintle
        actor['type_name'] = self.objects[actor['type_id']]
        if 'TheWorld' in actor['type_name']:  # World types are Vector Less
            return actor
        actor['vector'] = read_pos_vector(netstream)
        if 'Ball_Default' in actor['type_name'] or 'Car_Default' in actor['type_name']:
            actor['rotation'] = read_rot_vector(netstream)
        return actor
