from collections import OrderedDict

from pyrope.netstream_property_parsing import read_property_value, PropertyParsingError
from pyrope.utils import reverse_bytewise, BOOL, read_serialized_vector, read_byte_vector, read_serialized_int


class FrameParsingError(Exception):
    pass


class Frame:
    _actor_alive = {}  # Map of ActorID:Archtype shared across Frames

    def __init__(self):
        self.current = None
        self.delta = None
        self.actors = None

    def parse_frame(self, netstream, objects, propertymapper):
        self.current = reverse_bytewise(netstream.read('bits:32')).floatle
        self.delta = reverse_bytewise(netstream.read('bits:32')).floatle
        if self.current < 0.001 or self.delta < 0.001:
            raise FrameParsingError("Last Frame caused some offset")
        self.actors = self._parse_actors(netstream, objects, propertymapper)

    def _parse_actors(self, netstream, objects, propertymapper):
        # actors = {}  # TODO Maybe find a way to not rely on OrderedDict just for sorted json output
        actors = OrderedDict() # Although the slowdown is neglible compared to all the bit reading
        while True:  # Actor Replicating Loop
            startpos = netstream.pos
            actor_present = netstream.read(BOOL)

            if not actor_present:
                break

            actorid = reverse_bytewise(netstream.read('bits:10')).uintle
            channel = netstream.read(BOOL)
            if not channel:
                try:
                    shorttype = str(actorid) + 'd' + '_' + self._actor_alive[actorid].split('.')[-1].split(':')[-1]
                    actors[shorttype] = {'startpos': startpos,
                                         'actor_id': actorid,
                                         'actor_type': self._actor_alive[actorid],
                                         'open': channel}
                    del self._actor_alive[actorid]  # Delete from active actor list
                except KeyError:
                    raise FrameParsingError("Tried to delete non existent actor", actors)
                continue

            new = netstream.read(BOOL)
            if new:
                type_name, data = self._parse_new_actor(netstream, objects)
                self._actor_alive[actorid] = type_name
            else:
                try:
                    data = self._parse_existing_actor(netstream, self._actor_alive[actorid], objects, propertymapper)
                except PropertyParsingError as e:
                    e.args += ({'CurrFrameActors': actors},
                               {'ErrorActorType': self._actor_alive[actorid],
                                'ErrorActorId': actorid})
                    raise e
            if new:
                shorttype = str(actorid) + 'n' + '_' + self._actor_alive[actorid].split('.')[-1].split(':')[-1]
            else:
                shorttype = str(actorid) + 'e' + '_' + self._actor_alive[actorid].split('.')[-1].split(':')[-1]
            actors[shorttype] = {
                'startpos': startpos,
                'actor_id': actorid,
                'actor_type': self._actor_alive[actorid],
                #'open': channel,
                'new': new,
                'data': data}
        return actors

    def _parse_existing_actor(self, netstream, actor_type, objects, propertymapper):
        properties = {}
        while netstream.read(BOOL):
            property_id = read_serialized_int(netstream, propertymapper.get_property_max_id(actor_type))
            property_name = objects[propertymapper.get_property_name(actor_type, property_id)]
            try:
                property_value = read_property_value(property_name, netstream)
            except PropertyParsingError as e:
                e.args += ({"Props_till_err": properties},)
                raise e
            properties[property_name] = property_value
        return properties

    def _parse_new_actor(self, netstream, objects):
        actor = {}
        actor['flag'] = netstream.read(BOOL)
        type_id = reverse_bytewise(netstream.read('bits:32')).uintle
        type_name = objects[type_id]
        if 'TheWorld' in type_name:  # World types are Vector Less
            return type_name, actor
        actor['vector'] = read_serialized_vector(netstream)
        if 'Ball_Default' in type_name or 'Car_Default' in type_name:
            actor['rotation'] = read_byte_vector(netstream)
        return type_name, actor
