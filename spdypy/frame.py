# -*- coding: utf-8 -*-
"""
spdypy.frame
~~~~~~~~~~~~

Defines SPDYPy's internal representation of a SPDY frame.
"""
# Define our control frame types.
SYN_STREAM = 1
SYN_REPLY = 2
RST_STREAM = 3
SETTINGS = 4
PING = 6
GOAWAY = 7
HEADERS = 8
WINDOW_UPDATE = 9


class Frame(object):
    """
    A single SPDY frame.
    """
    def __init__(self):
        self.control = None
        self.version = None
        self.type = None
        self.flags = []
        self.data = None
        self.stream_id = None
