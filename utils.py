__author__ = 'temme.jan'

UINT_32 = 'uintle:32'
UINT_64 = 'uintle:64'
FLOAT_32 = 'floatle:32'


def read_string(bitstream):  # TODO OPTIONAL: CHECK IF PROPERLY NULL TERMINATED
    string_len = bitstream.read('intle:32')
    if string_len < 0:
        string_len *= -2
        return bitstream.read('bytes:'+str(string_len))[:-2].decode('utf-16')
    return bitstream.read('bytes:'+str(string_len))[:-1].decode('utf-8')
