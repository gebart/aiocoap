# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

from datetime import datetime

class TextDumper(object):
    """Plain text etwork data dumper

    A TextDumper can be used to log network traffic into a file that can be
    converted to a PCAP-NG file as described in its header.

    Currently, this discards information like addresses; it is unknown how that
    information can be transferred into a dump reader easily while
    simultaneously staying at application level and staying ignorant of
    particular underlying protocols' data structures.

    It can be used stand-alone (outside of the asyncio transport/protocol
    mechanisms) when instanciated only with an output file; in that case, us
    the :meth:datagram_received and :meth:sendto methods.

    To use it between an asyncio transport and protocol, use the
    :meth:endpointfactory method."""

    def __init__(self, outfile, protocol=None):
        self._outfile = outfile
        self._outfile.write("# Generated by aiocoap.dump %s\n"%datetime.now())
        self._outfile.write("# Convert to pcap-ng by using:\n#\n")
        self._outfile.write("""# text2pcap -n -u 5683,5683 -D -t "%Y-%m-%d %H:%M:%S."\n\n""")
        self._protocol = protocol
        self._transport = None

    @classmethod
    def endpointfactory(cls, outfile, actual_protocol):
        """This method returns a function suitable for passing to an asyncio
        loop's .create_datagram_endpoint method. It will place the TextDumper
        between the object and the transport, transparently dumping network
        traffic and passing it on together with other methods defined in the
        protocol/transport interface.

        If you need the actual protocol after generating the endpoint (which
        when using this method returns a TextDumper instead of an
        actual_protocol), you can access it using the protocol property."""

        def factory():
            dumper = cls(outfile, actual_protocol())
            return dumper
        return factory

    protocol = property(lambda self: self._protocol)

    # methods for both direct use and transport/protocol use

    def datagram_received(self, data, address):
        self._outfile.write("I %s 000 %s\n"%(datetime.now(), " ".join("%02x"%c for c in data)))
        if self._protocol is not None:
            self._protocol.datagram_received(data, address)

    def sendto(self, data, address):
        self._outfile.write("O %s 000 %s\n"%(datetime.now(), " ".join("%02x"%c for c in data)))
        if self._protocol is not None:
            # it's not an error to check for _protocol and not for _transport
            # here: if the protocol got hold of this fake transport by other
            # means than connection_made, writing before connection_made should
            # still create an error.
            self._transport.sendto(data, address)

    # passed-through properties and methods

    def connection_made(self, transport):
        self._transport = transport
        self._protocol.connection_made(self)

    _sock = property(lambda self: self._transport._sock)

    def close(self):
        self._outfile.close()
        self._transport.close()
