import bitstring

UINT_32 = 'uintle:32'
UINT_64 = 'uintle:64'
FLOAT_32 = 'floatle:32'


def read_file_meta(replay):
    header_size = replay.read(UINT_32)-8
    crc = replay.read('hex:32')
    version = str(replay.read(UINT_32)) + '.' + str(replay.read(UINT_32))
    return header_size, crc, version


def read_string(bitstream):
    string_len = str(bitstream.read(UINT_32))
    string_value = bitstream.read('bytes:'+string_len)[:-1]  # TODO OPTIONAL: CHECK IF PROPERLY NULL TERMINATED
    return string_value.decode('utf-8')


def decode_propertys(bitstream):
    propertys = {}
    while True:
        property = decode_property(bitstream)
        if property:
            propertys[property['key']] = property['value']
        else:
            return propertys


def decode_property(bitstream):
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
            decode_propertys(bitstream)
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

if __name__ == '__main__':
    replay = bitstring.ConstBitStream(filename="testfiles/r3.replay")
    size, crc, ver = read_file_meta(replay)
    print('Headersize:\t%d\nCRC:\t\t%s\nVersion:\t%s' % (size, crc, ver))
    print(read_string(replay))
    header = decode_propertys(replay)