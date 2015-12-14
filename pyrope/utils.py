import math
import bitstring
UINT_32 = 'uintle:32'
UINT_64 = 'uintle:64'
FLOAT_LE_32 = 'floatle:32'
FLOAT_BE_32 = 'floatbe:32'
BOOL = 'bool'


class ParsingError(Exception):
    pass


def read_string(bitstream):  # TODO OPTIONAL: CHECK IF PROPERLY NULL TERMINATED
    string_len = bitstream.read('intle:32')
    if string_len < 0:
        string_len *= -2
        return bitstream.read('bytes:'+str(string_len))[:-2].decode('utf-16')
    return bitstream.read('bytes:'+str(string_len))[:-1].decode('utf-8')


def reverse_bytewise(bitstream, dbg=False):
    # start = time()
    result = []
    if dbg: print(bitstream.bin)
    for byte in bitstream.tobytes():
        if dbg: print(hex(byte))
        result.append(reverse_byte(byte))
    reverse_bytes = bitstring.ConstBitStream(bytes=result)
    # delta = time() - start
    # print('method three took', delta)
    return reverse_bytes


def reverse_byte(x):
    x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
    x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
    x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
    return x


def read_serialized_int(bitstream, max_val=19):
    max_bits = math.ceil(math.log(max_val, 2))
    value = 0
    i = 0
    while i < max_bits and (value + (1 << i) <= max_val):
        bit = bitstream.read(BOOL)
        if bit:
            value += (1 << i)
        # print(bin(value))
        i += 1
    return value


def read_serialized_vector(bitstream):
    numbits = read_serialized_int(bitstream)
    bias = 1 << (numbits+1)
    max = numbits + 2
    dx = reverse_bytewise(bitstream.read(max)).intle
    dy = reverse_bytewise(bitstream.read(max)).intle
    dz = reverse_bytewise(bitstream.read(max)).intle
    x = dx-bias
    y = dy-bias
    z = dz-bias
    return x, y, z


def read_byte_vector(bitstream):
    x = y = z = 0
    if bitstream.read(BOOL):
        x = reverse_byte(bitstream.read('uint:8'))
    if bitstream.read(BOOL):
        y = reverse_byte(bitstream.read('uint:8'))
    if bitstream.read(BOOL):
        z = reverse_byte(bitstream.read('uint:8'))
    return x, y, z


def read_float_vector(bitstream):
    x = _read_serialized_float(1, 16, bitstream)
    y = _read_serialized_float(1, 16, bitstream)
    z = _read_serialized_float(1, 16, bitstream)
    return x, y, z


def _read_serialized_float(max_value, numbits, bitstream):
    '''
    I dont know whats exactly happening here. Thanks again to https://github.com/jjbott/RocketLeagueReplayParser from
    where i blatantly copied that part
    '''
    max_bit_value = (1 << (numbits - 1)) - 1
    bias = (1 << (numbits - 1))
    ser_int_max = (1 << (numbits - 0))
    delta = read_serialized_int(bitstream, ser_int_max)
    unscaled_value = delta - bias
    if max_value > max_bit_value:
        inv_scale = max_value / max_bit_value
        value = unscaled_value * inv_scale
    else:
        scale = max_bit_value / max_value
        inv_scale = 1.0/scale
        value = unscaled_value * inv_scale
    return value