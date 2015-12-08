import bitstring
from parse_header import HeaderParser


if __name__ == '__main__':
    header = HeaderParser("testfiles/r3.replay").getHeader()
    print(header)