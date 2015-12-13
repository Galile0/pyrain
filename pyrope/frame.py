from pyrope.netstream_property_parsing import read_property_value, PropertyParsingError
from pyrope.utils import reverse_bytewise, BOOL, read_serialized_vector, read_byte_vector, read_serialized_int


class FrameParsingError(Exception):
    pass


class Frame:
    actor_alive = {}  # Map of ActorID:Archtype shared across Frames
    actor_appeared = {}

    def __init__(self, framenum):
        self.framenum = framenum
        self.current = None
        self.delta = None
        self.actors = []

    def parse_frame(self, netstream, objects, propertymapper):
        self.current = reverse_bytewise(netstream.read('bits:32')).floatle
        self.delta = reverse_bytewise(netstream.read('bits:32')).floatle
        self.actors = self._parse_actors(netstream, objects, propertymapper)

    def _parse_actors(self, netstream, objects, propertymapper):
        actors = []
        while True:  # Actor Replicating Loop
            startpos = netstream.pos
            actor_present = netstream.read(BOOL)

            if not actor_present:
                break

            actorid = reverse_bytewise(netstream.read('bits:10')).uintle
            channel = netstream.read(BOOL)
            if not channel:
                try:
                    del self.actor_alive[actorid]  # Delete from active actor list
                except KeyError:
                    raise FrameParsingError("Tried to delete non existent actor", actors)
                continue

            new = netstream.read(BOOL)
            if new:
                data = self._parse_new_actor(netstream, objects)
                self.actor_appeared[actorid] = data['type_name']
                self.actor_alive[actorid] = data['type_name']  # Add actor to currently exist.
            else:
                try:
                    data = self._parse_existing_actor(netstream, self.actor_alive[actorid], objects, propertymapper)
                except PropertyParsingError as e:
                    e.args += ({"CurrFrameActors": actors},
                               {"ErrorActorType": self.actor_alive[actorid],
                                "ErrorActorId": actorid})
                    raise e
            actors.append({
                'startpos': startpos,
                'actor_type': self.actor_alive[actorid],
                'actor_id': actorid,
                'open': channel,
                'new': new,
                'data': data})
        return actors

    def _parse_existing_actor(self, netstream, actor_type, objects, propertymapper):
        properties = []
        while netstream.read(BOOL):
            property_id = read_serialized_int(netstream, propertymapper.get_property_max_id(actor_type))
            property_name = objects[propertymapper.get_property_name(actor_type, property_id)]
            try:
                property_value = read_property_value(property_name, netstream)
            except PropertyParsingError as e:
                properties.append({
                    'property_id': property_id,
                    'property_name': property_name})
                e.args += ("Properties so far: %s" % properties,)
                raise e
            properties.append({'property_id': property_id,
                               'property_name': property_name,
                               'property_value': property_value})
        return properties

    def _parse_new_actor(self, netstream, objects):
        actor = {}
        actor['unknown_flag'] = netstream.read(BOOL)
        actor['type_id'] = reverse_bytewise(netstream.read('bits:32')).uintle
        actor['type_name'] = objects[actor['type_id']]
        if 'TheWorld' in actor['type_name']:  # World types are Vector Less
            return actor
        actor['vector'] = read_serialized_vector(netstream)
        if 'Ball_Default' in actor['type_name'] or 'Car_Default' in actor['type_name']:
            actor['rotation'] = read_byte_vector(netstream)
        return actor
