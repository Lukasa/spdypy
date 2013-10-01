# -*- coding: utf-8 -*-
"""
spdypy.frame
~~~~~~~~~~~~

Defines SPDYPy's internal representation of a SPDY frame.
"""
import struct


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
    flags = set()

    if frame_type in (None, SYN_REPLY, HEADERS):
        if byte & 0x01:
            flags.add(FLAG_FIN)

    elif frame_type == SYN_STREAM:
        if byte & 0x01:
            flags.add(FLAG_FIN)
        if byte & 0x02:
            flags.add(FLAG_UNIDIRECTIONAL)

    elif frame_type == SETTINGS:
        if byte & 0x01:
            flags.add(FLAG_CLEAR_SETTINGS)

    return flags


class Frame(object):
    """
    A single SPDY frame. This is effectively an abstract base class for the
    various SPDY frame classes.
    """
    def __init__(self):
        self.control = None
        self.version = None
        self.type = None
        self.flags = set()
        self.data = None
        self.stream_id = None

    def build_flags(self, flag_byte):
        """
        This method should take a flag byte, and then populate the flags set
        on the object.
        """
        raise NotImplementedError("This is an abstract base class.")

    def build_data(self, data_buffer):
        """
        This method builds the relevant instance variables from the data buffer
        that makes up the frame body.
        """
        raise NotImplementedError("This is an abtract base class.")


class SYNStreamFrame(Frame):
    """
    A single SYN_STREAM frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.

        :param flag_byte: The byte containing the flags.
        """
        if flag_byte & 0x01:
            self.flags.add(FLAG_FIN)
        if flag_byte & 0x02:
            self.flags.add(FLAG_UNIDIRECTIONAL)

    def build_data(self, data_buffer):
        """
        Build the SYN_STREAM body fields.
        """
        fields = struct.unpack("!LLL", data_buffer[0:12])
        self.stream_id = fields[0] & 0x7FFFFFFF
        self.assoc_stream_id = fields[1] & 0x7FFFFFFF
        self.priority = (fields[2] & 0xE0000000) >> 29

        self.name_value_block = data_buffer[12:]
