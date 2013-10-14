# -*- coding: utf-8 -*-
"""
spdypy.frame
~~~~~~~~~~~~

Defines SPDYPy's internal representation of a SPDY frame.
"""
import struct
import zlib
from collections import namedtuple


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
FLAG_SETTINGS_PERSIST_VALUE = 'FLAG_SETTINGS_PERSIST_VALUE'
FLAG_SETTINGS_PERSISTED = 'FLAG_SETTINGS_PERSISTED'

# Define the settings IDs.
SETTINGS_UPLOAD_BANDWIDTH = 1
SETTINGS_DOWNLOAD_BANDWIDTH = 2
SETTINGS_ROUND_TRIP_TIME = 3
SETTINGS_MAX_CONCURRENT_STREAMS = 4
SETTINGS_CURRENT_CWND = 5
SETTINGS_DOWNLOAD_RETRANS_RATE = 6
SETTINGS_INITIAL_WINDOW_SIZE = 7
SETTINGS_CLIENT_CERTIFICATE_VECTOR_SIZE = 8


# Define our NamedTuple for containing frame settings.
Settings = namedtuple('Settings', ['id', 'value', 'flags'])


def from_bytes(buffer, decompressor=None):
    """
    Build a Frame object from the buffer. Returns the correct Frame and the
    number of bytes consumed from the buffer.

    :param buffer: The byte buffer that represents the frame.
    :param decompressor: Optionally provide a decompressor for the NV block.
    """
    control = buffer[0] & 0x80

    # Build the fields from the first 4 bytes, then pass the remainder off to
    # the relevant class.
    if control:
        fields = struct.unpack("!HH", buffer[0:4])
        version = fields[0] & 0x7FFF
        frame_type = fields[1]

        frame = frame_from_type.get(frame_type, Frame)()

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
    frame.build_data(buffer[8:8 + length], decompressor)

    return (frame, 8 + length)


def parse_nv_block(decompressor, nv_bytes):
    """
    This function parses the compressed name-value header block.

    :param decompressor: A ``zlib`` decompression object from the stream.
    :param nv_bytes: The bytes comprising the name-value header block.
    """
    headers = {}

    if not nv_bytes:
        return headers

    data = decompressor.decompress(nv_bytes)

    # Get the number of NV pairs.
    num = struct.unpack("!L", data[0:4])[0]

    data = data[4:]

    # Remaining data.
    for i in range(0, num):
        # Get the length of the name, in octets.
        name_len = struct.unpack("!L", data[0:4])[0]
        name = data[4:4+name_len]

        data = data[4+name_len:]

        # Now the length of the value.
        value_len = struct.unpack("!L", data[0:4])[0]
        value = data[4:4+value_len]

        data = data[4+value_len:]

        # You can get multiple values in a header, they're separated by
        # null bytes. Use a list to store the multiple values.
        vals = value.split(b'\0')
        if len(vals) == 1:
            vals = vals[0]

        headers[name] = vals

    return headers


def build_nv_block(compressor, nv_headers):
    """
    Build the compressed Name-Value header block.

    :param compressor: The zlib compressor object for the stream.
    :param nv_headers: The dictionary representing the NV header block.
    """
    # First, stringify!
    data = struct.pack("!L", len(nv_headers))

    for name, value in nv_headers.items():
        data += struct.pack("!L", len(name))
        data += name

        if isinstance(value, list):
            joined = b'\0'.join(value)
            data += struct.pack("!L", len(joined))
            data += joined
        else:
            data += struct.pack("!L", len(value))
            data += value

    # Now compress like a champ.
    compressed = compressor.compress(data)
    compressed += compressor.flush(zlib.Z_SYNC_FLUSH)

    return compressed


class Frame(object):
    """
    A single SPDY frame. This is effectively an abstract base class for the
    various SPDY frame classes.
    """
    def __init__(self):
        self.control = None
        self.version = None
        self.flags = set()
        self.data = None
        self.stream_id = None

    def build_flags(self, flag_byte):
        """
        This method should take a flag byte, and then populate the flags set
        on the object.
        """
        raise NotImplementedError("This is an abstract base class.")

    def build_data(self, data_buffer, decompressor):
        """
        This method builds the relevant instance variables from the data buffer
        that makes up the frame body.
        """
        raise NotImplementedError("This is an abtract base class.")

    def to_bytes(self):
        """
        This method re-serialises the frame into a bytestring suitable for
        sending on the wire.
        """
        raise NotImplementedError("This is an abstract base class.")


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

    def build_data(self, data_buffer, decompressor, stream):
        """
        Build the SYN_XXX body fields. Set 'stream' to True if this is a
        SYN_STREAM frame, otherwise set to False.
        """
        if stream:
            fields = struct.unpack("!LLL", data_buffer[0:12])
        else:
            fields = struct.unpack("!L", data_buffer[0:4])

        self.stream_id = fields[0] & 0x7FFFFFFF

        if stream:
            self.assoc_stream_id = fields[1] & 0x7FFFFFFF
            self.priority = (fields[2] & 0xE0000000) >> 29
            self.headers = parse_nv_block(decompressor, data_buffer[12:])
        else:
            self.headers = parse_nv_block(decompressor, data_buffer[4:])


class SYNStreamFrame(SYNMixin, Frame):
    """
    A single SYN_STREAM frame.
    """
    def build_data(self, data_buffer, decompressor):
        super(SYNStreamFrame, self).build_data(data_buffer, decompressor, True)


class SYNReplyFrame(SYNMixin, Frame):
    """
    A single SYN_REPLY frame.
    """
    def build_data(self, data_buffer, decompressor):
        super(SYNReplyFrame, self).build_data(data_buffer, decompressor, False)


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

    def build_data(self, data_buffer, *args):
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

    def build_data(self, data_buffer, *args):
        """
        Build the SETTINGS body fields.
        """
        self.settings = []

        # The first 32 bits define the number of setting values to expect.
        fields = struct.unpack("!L", data_buffer[0:4])[0]
        field_len = fields * 8

        # Each of the ID/value pairs is 64 bits long. Expect that many of them.
        struct_str = '!' + ('LL' * fields)
        setting_pairs = struct.unpack(struct_str, data_buffer[4:4 + field_len])

        for i in range(fields):
            # Handle the flags first.
            field_flags = set()

            if setting_pairs[i * 2] & 0x01000000:
                field_flags.add(FLAG_SETTINGS_PERSIST_VALUE)
            if setting_pairs[i * 2] & 0x02000000:
                field_flags.add(FLAG_SETTINGS_PERSISTED)

            field_id = setting_pairs[i * 2] & 0x00FFFFFF
            field_value = setting_pairs[(i * 2) + 1]

            # Add the field.
            self.settings.append(Settings(field_id, field_value, field_flags))

        return


class PingFrame(Frame):
    """
    A single PING frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.
        """
        if flag_byte != 0:
            raise ValueError("PING never defines flags.")

    def build_data(self, data_buffer, *args):
        """
        Build the PING body fields.
        """
        self.ping_id = struct.unpack("!L", data_buffer[0:4])[0]

        return


class GoAwayFrame(Frame):
    """
    A single GOAWAY frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.
        """
        if flag_byte != 0:
            raise ValueError("GOAWAY never defines flags.")

    def build_data(self, data_buffer, *args):
        """
        Build the GOAWAY body fields.
        """
        fields = struct.unpack("!LL", data_buffer[0:8])
        self.last_good_stream_id = fields[0] & 0x7FFFFFFF
        self.status_code = fields[1]

        return


class HeadersFrame(Frame):
    """
    A single HEADERS frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.
        """
        if flag_byte & 0x01:
            self.flags.add(FLAG_FIN)

    def build_data(self, data_buffer, decompressor):
        """
        Build the HEADERS body fields.
        """
        fields = struct.unpack("!L", data_buffer[0:4])
        self.stream_id = fields[0] & 0x7FFFFFFF

        # We now have the Name/Value header block.
        self.headers = parse_nv_block(decompressor, data_buffer[4:])


class WindowUpdateFrame(Frame):
    """
    A single WINDOW_UPDATE frame.
    """
    def build_flags(self, flag_byte):
        """
        Build the flags for this frame from the given byte.
        """
        if flag_byte != 0:
            raise ValueError("WINDOW_UPDATE never defines flags.")

    def build_data(self, data_buffer, *args):
        """
        Build the WINDOW_UPDATE body fields.
        """
        fields = struct.unpack("!LL", data_buffer[0:8])

        self.stream_id = fields[0] & 0x7FFFFFFF
        self.delta_window_size = fields[1] & 0x7FFFFFFF


# Map frame indicator bytes to frame objects.
frame_from_type = {
    SYN_STREAM: SYNStreamFrame,
    SYN_REPLY: SYNReplyFrame,
    RST_STREAM: RSTStreamFrame,
    SETTINGS: SettingsFrame,
    PING: PingFrame,
    GOAWAY: GoAwayFrame,
    HEADERS: HeadersFrame,
    WINDOW_UPDATE: WindowUpdateFrame,
}
