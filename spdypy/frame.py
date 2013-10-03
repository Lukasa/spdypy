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


def from_bytes(buffer):
    """
    Build a Frame object from the buffer. Returns the correct Frame and the
    number of bytes consumed from the buffer.

    :param buffer: The byte buffer that represents the frame.
    """
    control = buffer[0] & 0x80

    # Build the fields from the first 4 bytes, then pass the remainder off to
    # the relevant class.
    if control:
        fields = struct.unpack("!HH", buffer[0:4])
        version = fields[0] & 0x7FFF
        frame_type = fields[1]

        if frame_type == SYN_STREAM:
            frame = SYNStreamFrame()
        else:
            frame = Frame()

        # Assign the fields we've already parsed.
        frame.control = True
        frame.version = version
    else:
        stream_id = struct.unpack("!L", buffer[0:4])[0] & 0x7FFFFFFF

        frame = Frame()
        frame.stream_id = stream_id

    # Let the frame build its flags up.
    frame.build_flags(buffer[4])

    # Get the length.
    length = struct.unpack("!L", buffer[4:8])[0] & 0x00FFFFFF

    # Then pass the remaining data to the data builder.
    frame.build_data(buffer[8:8 + length])

    return (frame, 8 + length)


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


class SYNMixin(object):
    """
    This mixin is used to generate the SYNStreamFrame and SYNReplyFrame
    classes. These classes reflect frames that have identical structures, and
    so will have identical implementations for a number of their methods.
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


class SYNStreamFrame(SYNMixin, Frame):
    """
    A single SYN_STREAM frame.
    """
    pass


class SYNReplyFrame(SYNMixin, Frame):
    """
    A single SYN_REPLY frame.
    """
    pass


class RSTStreamFrame(Frame):
    """
    A single RST_STREAM frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.
        """
        if flag_byte != 0:
            raise ValueError("RST_STREAM never defines flags.")

    def build_data(self, data_buffer):
        """
        Build the RST_STREAM body fields.
        """
        fields = struct.unpack("!LL", data_buffer[0:8])

        self.stream_id = fields[0] & 0x7FFFFFFF

        # Check the status code field as well.
        if not 0 < fields[1] < 12:
            raise RuntimeError("Invalid status code.")

        self.status_code = fields[1]

        return


class SettingsFrame(Frame):
    """
    A single SETTINGS frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.
        """
        if flag_byte & 0x01:
            self.flags.add(FLAG_CLEAR_SETTINGS)
