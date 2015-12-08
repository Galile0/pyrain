from utils import read_string, UINT_32, UINT_64, FLOAT_32
import bitstring


class HeaderParser:
    def __init__(self, replay_file):
        self.replay = bitstring.ConstBitStream(filename=replay_file)

    def getHeader(self):
        self.replay.bytepos = 0 # Ensure we always start at the Top of the File
        header = {}
        size, crc, version = self._read_file_meta(self.replay)
        header['size'] = size
        header['crc'] = crc
        header['version'] = version
        header['name'] = read_string(self.replay)
        header['propertys'] = self._decode_propertys(self.replay)
        return header

    def _read_file_meta(self, replay):
        header_size = replay.read(UINT_32)-8
        crc = replay.read('hex:32')
        version = str(replay.read(UINT_32)) + '.' + str(replay.read(UINT_32))
        return header_size, crc, version

    def _decode_propertys(self, bitstream):
        propertys = {}
        while True:
            property = self._decode_property(bitstream)
            if property:
                propertys[property['key']] = property['value']
            else:
                return propertys


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
            property_value = bitstream.read(FLOAT_32)
        elif property_type == 'NameProperty':
            property_value = read_string(bitstream)
        elif property_type == 'ArrayProperty':
            array_length = bitstream.read(UINT_32)
            property_value = [
                self._decode_propertys(bitstream)
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