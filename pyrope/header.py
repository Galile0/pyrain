from pyrope.utils import read_string, UINT_32, UINT_64, FLOAT_LE_32


class Header:
    def __init__(self, bitstream):
        self.raw = bitstream
        self.parsed = None

    def parse(self):
        if not self.parsed:
            read_string(self.raw)  # Read and discard TAGame.Replay_Soccar_TA
            self.parsed = self._decode_properties(self.raw)
        return self.parsed

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


class HeaderParsingError(Exception):
    pass
