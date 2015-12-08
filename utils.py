__author__ = 'temme.jan'

UINT_32 = 'uintle:32'
UINT_64 = 'uintle:64'
FLOAT_32 = 'floatle:32'


def read_string(bitstream):
    string_len = str(bitstream.read(UINT_32))
    string_value = bitstream.read('bytes:'+string_len)[:-1]  # TODO OPTIONAL: CHECK IF PROPERLY NULL TERMINATED
    return string_value.decode('utf-8')
