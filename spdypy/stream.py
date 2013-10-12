# -*- coding: utf-8 -*-
"""
spdypy.stream
~~~~~~~~~~~~~

Abstractions for SPDY streams.
"""


class Stream(object):
    """
    A SPDY connection is made up of many streams. Each stream communicates by
    sending some nonzero number of frames, beginning with a SYN_STREAM and
    ending with a RST_STREAM frame.

    The stream abstraction provides a system for wrapping HTTP connections in
    frames for sending down SPDY connections. They are a purely internal
    abstraction, and not intended for use by end-users of SPDYPy.

    :param stream_id: The stream_id for this stream.
    """
    def __init__(self, stream_id):
        self.stream_id = stream_id
