# -*- coding: utf-8 -*-
"""
spdypy.stream
~~~~~~~~~~~~~

Abstractions for SPDY streams.
"""
from .frame import SYNStreamFrame


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

    def open_stream(self, priority, associated_stream=None):
        """
        Builds the frames necessary to open a SPDY stream. Returns the frames
        as a bytestring, ready for transmission on the wire.

        :param priority: The priority of this stream, from 0 to 7. 0 is the
                         highest priority, 7 the lowest.
        :param associated_stream: (optional) The stream this stream is
                                  associated to.
        """
        assoc_id = associated_stream.stream_id if associated_stream else None

        syn = SYNStreamFrame()
        syn.control = True
        syn.version = self.version
        syn.assoc_stream_id = assoc_id
        syn.priority = priority
