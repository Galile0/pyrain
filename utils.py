import math
import bitstring
UINT_32 = 'uintle:32'
UINT_64 = 'uintle:64'
FLOAT_LE_32 = 'floatle:32'
FLOAT_BE_32 = 'floatbe:32'
BOOL = 'bool'


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


def read_pos_vector(bitstream):
    # pos_start = netstream.pos
    length = read_serialized_int(bitstream)+2
    # l_bits = netstream.pos - pos_start
    # print("Length %d coded in %d bits" % (length, l_bits))
    x = reverse_bytewise(bitstream.read(length)).uintle
    y = reverse_bytewise(bitstream.read(length)).uintle
    z = reverse_bytewise(bitstream.read(length)).uintle
    # netstream.pos = pos
    return (x, y, z)


def read_rot_vector(bitstream):
    x = y = z = 0
    if bitstream.read(BOOL):
        x = reverse_byte(bitstream.read('uint:8'))
    if bitstream.read(BOOL):
        y = reverse_byte(bitstream.read('uint:8'))
    if bitstream.read(BOOL):
        z = reverse_byte(bitstream.read('uint:8'))
    return x, y, z

if __name__ == '__main__':
    v1 = bitstring.ConstBitStream('0b0011000000000000010000000001110000110100000001')
    v2 = bitstring.ConstBitStream('0x601017b')

    print(read_pos_vector(v1))

    '''
ZorMOnkeys version of serialized int reading (Max value of 20 in code, 19 reported to work better)
public Int32 ReadInt32Max(Int32 maxValue)
{
    var maxBits = Math.Floor(Math.Log10(maxValue) / Math.Log10(2)) + 1;

    Int32 value = 0;
    for(int i = 0; i < maxBits && (value + (1<< i)) <= maxValue; ++i)
    {
        value += (ReadBit() ? 1: 0) << i;
    }

    if ( value > maxValue)
    {
        throw new Exception("ReadInt32Max overflowed!");
    }

    return value;
}

coded after FBitReader::SerializeInt in ue
'''