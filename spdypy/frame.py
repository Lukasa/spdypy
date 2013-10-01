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

# Define the flags we know about.
FLAG_FIN = 'FLAG_FIN'
FLAG_UNIDIRECTIONAL = 'FLAG_UNIDIRECTIONAL'
FLAG_CLEAR_SETTINGS = 'FLAG_CLEAR_SETTINGS'


def flags(byte, frame_type=None):
    """
    Given the flag byte and the frame type, return the flags that have been
    set. If the frame type is not set, assumes a data frame.

    :param byte: The flag byte.
    :param frame_type: The control frame type, or None if the frame is a data
                       frame.
    """
    flags = []

    if frame_type in (None, SYN_REPLY, HEADERS):
        if byte & 0x01:
            flags.append(FLAG_FIN)

    elif frame_type == SYN_STREAM:
        if byte & 0x01:
            flags.append(FLAG_FIN)
        if byte & 0x02:
            flags.append(FLAG_UNIDIRECTIONAL)

    elif frame_type == SETTINGS:
        if byte & 0x01:
            flags.append(FLAG_CLEAR_SETTINGS)

    return flags


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
