import bitstring


class NetstreamParser:

    def __init__(self, netstream):
        inverted_netstream = bitstring.BitArray()
        for byte in netstream.unpack('bits:8'*(netstream.length/8)):
            byte.reverse()
            inverted_netstream.append(byte)
        self.netstream = bitstring.ConstBitStream(inverted_netstream)