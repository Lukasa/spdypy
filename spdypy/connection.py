# -*- coding: utf-8 -*-
"""
spdypy.connection
~~~~~~~~~~~~~~~~~

Contains the code necessary for working with SPDY connections.
"""
import ssl
import socket
import select
import zlib
from .stream import Stream
from .frame import from_bytes
from .data import SPDY_3_ZLIB_DICT


# Define some states for SPDYConnections.
NEW = 'NEW'


class SPDYConnection(object):
    """
    A representation of a single SPDY connection to a remote server. This
    object takes responsibility for managing the complexities of the SPDY
    protocol, including streams and options. This complexity is abstracted
    away into an interface that broadly looks like the standard library's
    HTTPSConnection class.

    :param host: The host to establish a connection to.
    """
    def __init__(self, host):
        self.host = host
        self._state = NEW
        self._context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self._sck = None
        self._streams = {}
        self._next_stream_id = 1
        self._last_stream_id = None
        self._compressor = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        self._decompressor = zlib.decompressobj(zdict=SPDY_3_ZLIB_DICT)

        # Set up the initial SSL context.
        self._context.set_default_verify_paths()
        self._context.set_npn_protocols(['http/1.1', 'spdy/3', 'spdy/3.1'])

    def request(self, method, path, body=None, headers={}):
        """
        This will send a request to the server using the HTTP request method
        ``method`` and the selector ``path``. If the ``body`` argument is
        present, it should be a string or bytes object of data to send after
        the headers are finished. Strings are encoded as ISO-8859-1, the
        default charset for HTTP. To use other encodings, pass a bytes object.
        The Content-Length header is set to the length of the string.

        The ``headers`` object should be a mapping of extra HTTP headers to
        send with the request.
        """
        pass

    def putrequest(self, request, selector, **kwargs):
        """
        This emulates the HTTPConnection ``putrequest()`` method, and allows
        for sending a SPDY request in stages. Due to the streamed nature of
        SPDY, this method does not actually send the request in question,
        but begins the building up of structures necessary to send the request.

        This returns the stream id, for use in the later methods.

        :param request: The request string, e.g. GET.
        :param selector: The path selector, beginning with a '/'.
        """
        self._connect()

        # Convert the request string and selector to bytes, if they aren't
        # already.
        request = request if isinstance(request, bytes) else request.encode('utf-8')
        selector = selector if isinstance(selector, bytes) else selector.encode('utf-8')

        # Begin by allocating a new stream object and giving it the next stream
        # ID.
        stream_id = self._next_stream_id
        stream = Stream(stream_id,
                        version=3,
                        compressor=self._compressor,
                        decompressor=self._decompressor)
        stream.open_stream(7)

        # Give the stream the necessary headers.
        stream.add_header(b':method', request)
        stream.add_header(b':path', selector)
        stream.add_header(b':version', b'HTTP/1.1')
        stream.add_header(b':host', self.host.encode('utf-8'))
        stream.add_header(b':scheme', b'https')

        # Increase the next stream ID, keeping it odd.
        self._next_stream_id += 2

        # Store the stream object.
        self._streams[stream_id] = stream

        return stream_id

    def putheader(self, header, argument, stream_id=None):
        """
        Emulates the HTTPConnection ``putheader()`` method. Because at this
        point we haven't actually opened a SPDY connection, this continues to
        add headers to the outstanding SPDY stream.

        :param header: The header key.
        :param argument: The header value. May be a list of values.
        :param stream_id: (Optional) The stream to add headers to. If not
                          provided, the last-created stream is chosen.
        """
        # Convert the header and argument to bytes if they aren't already.
        header = header if isinstance(header, bytes) else header.encode('utf-8')
        argument = argument if isinstance(argument, bytes) else argument.encode('utf-8')

        stream_id = stream_id if stream_id else max(self._streams.keys())
        stream = self._streams[stream_id]
        stream.add_header(header, argument)
        return

    def endheaders(self, message_body=None, stream_id=None):
        """
        Emulates the HTTPConnection ``endheaders`` method. This method defines
        the point at which we can actually send any SPDY data. The previously
        defined headers will be sent. If ``message_body`` is provided, a
        ``Content-Length`` header will automatically be set and the data will
        be sent as well. Otherwise, only the connection will be set up.

        :param message_body: (Optional) Body data to send. If provided, it is
                             assumed that no more body data will be sent.
        :param stream_id: (Optional) The stream to end the headers of. If not
                          provided, the last-created stream is chosen.
        """
        stream_id = stream_id if stream_id else max(self._streams.keys())
        stream = self._streams[stream_id]

        if message_body is not None:
            length = len(message_body)
            stream.add_header(b'content-length', str(length).encode('utf-8'))
            stream.prepare_data(message_body, last=True)

        stream.send_outstanding(self._sck)

    def _read_outstanding(self, timeout):
        """
        Reads outstanding data from the socket. For now, for debugging
        purposes, it returns the data directly to the caller. Later it'll
        farm out to stream objects.

        :param timeout: The maximum amount of time to wait for another frame.
        """
        readable, _, _ = select.select([self._sck], [], [], 0.5)
        if not readable:
            return []

        data = self._sck.read(65535)
        frames = []

        while data:
            frame, cons = from_bytes(data, self._decompressor)
            frames.append(frame)
            data = data[cons:]

        return frames

    def _connect(self):
        """
        This method will open a socket connection to the remote server and
        perform the SSL handshake necessary to open a SPDY connection. This
        method is a no-op if there is already an open socket, so it should be
        safe to call in all circumstances.
        """
        if self._sck is not None:
            return

        # We have to look up the host. For now, assume port 443.
        addrs = socket.getaddrinfo(self.host, 443)

        # Later on we'll want to try a number of these, but for now just use
        # the first.
        address = addrs[0][4]

        sck = socket.socket()
        sck = self._context.wrap_socket(sck, server_hostname=self.host)
        sck.connect(address)

        self._sck = sck
