# -*- coding: utf-8 -*-
"""
spdypy.stream
~~~~~~~~~~~~~

Abstractions for SPDY streams.
"""
import collections
import zlib
from .frame import SYNStreamFrame, DataFrame, FLAG_FIN
from .data import SPDY_3_ZLIB_DICT


class Stream(object):
    """
    A SPDY connection is made up of many streams. Each stream communicates by
    sending some nonzero number of frames, beginning with a SYN_STREAM and
    ending with a RST_STREAM frame.

    The stream abstraction provides a system for wrapping HTTP connections in
    frames for sending down SPDY connections. They are a purely internal
    abstraction, and not intended for use by end-users of SPDYPy.

    :param stream_id: The stream_id for this stream.
    :param version: The SPDY version this stream is for.
    """
    def __init__(self, stream_id, version):
        self.stream_id = stream_id
        self.version = version
        self._queued_frames = collections.deque()
        self._compressor = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        self._decompressor = zlib.decompressobj(zdict=SPDY_3_ZLIB_DICT)

    def open_stream(self, priority, associated_stream=None):
        """
        Builds the frames necessary to open a SPDY stream. Stores them in the
        queued frames object.

        :param priority: The priority of this stream, from 0 to 7. 0 is the
                         highest priority, 7 the lowest.
        :param associated_stream: (optional) The stream this stream is
                                  associated to.
        """
        assoc_id = associated_stream.stream_id if associated_stream else None

        syn = SYNStreamFrame()
        syn.version = self.version
        syn.stream_id = self.stream_id
        syn.assoc_stream_id = assoc_id
        syn.priority = priority

        # Assume this will be the last frame unless we find out otherwise.
        syn.flags.add(FLAG_FIN)

        self._queued_frames.append(syn)

    def add_header(self, key, value):
        """
        Adds a SPDY header to the stream. For now this assumes that the first
        outstanding frame in the queue is one that has headers on it. Later,
        this method will be smarter.

        :param key: The header key.
        :param value: The header value.
        """
        frame = self._queued_frames[0]
        frame.headers[key] = value

    def prepare_data(self, data, last=False):
        """
        Prepares some data in a data frame.

        :param data: The data to send.
        :param last: (Optional) Whether this is the last data frame.
        """
        frame = DataFrame()
        frame.stream_id = self.stream_id

        # Remove any FLAG_FIN earlier in the queue.
        for frame in self._queued_frames:
            frame.flags.discard(FLAG_FIN)

        if last:
            frame.flags.add(FLAG_FIN)

        frame.data = data

        self._queued_frames.append(frame)

    def send_outstanding(self, connection):
        """
        Sends any outstanding frames on a given connection.

        :param connection: The connection to send the frames on.
        """
        frame = self._next_frame()

        while frame is not None:
            data = frame.to_bytes(self._compressor)
            connection.send(data)

            frame = self._next_frame()

    def _next_frame(self):
        """
        Utility method for returning the next frame from the frame queue.
        """
        try:
            return self._queued_frames.popleft()
        except IndexError:
            return None
