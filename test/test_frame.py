# -*- coding: utf-8 -*-
"""
test/test_frame
~~~~~~~~~~~~~~~
Tests of the SPDY frame.
"""
import zlib
from spdypy.frame import *
from spdypy.data import SPDY_3_ZLIB_DICT
from pytest import raises


class NullDecompressor(object):
    """
    Useful decompressor that just returns the data put in.
    """
    def decompress(self, data):
        return data


class TestFrame(object):
    def test_can_create_blank_frame(self):
        assert Frame()

    def test_frame_default_field_values(self):
        fr = Frame()
        assert fr.control is None
        assert fr.version is None
        assert fr.flags == set()
        assert fr.data is None
        assert fr.stream_id is None

    def test_frame_is_abc(self):
        fr = Frame()

        with raises(NotImplementedError):
            fr.build_flags(0x00)

        with raises(NotImplementedError):
            fr.build_data('', None)

        with raises(NotImplementedError):
            fr.to_bytes()


class TestFromBytes(object):
    def __test_syn_xxx_frame_good(self, frame_bytes, frametype):
        # Prepare for the NV block.
        indata = b'\x00\x00\x00\x02\x00\x00\x00\x01a\x00\x00\x00\x01b\x00\x00\x00\x01c\x00\x00\x00\x03d\x00e'
        compobj = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        compressed = compobj.compress(indata)
        compressed += compobj.flush(zlib.Z_SYNC_FLUSH)
        decobj = zlib.decompressobj(zdict=SPDY_3_ZLIB_DICT)
        nv_expected = {b'a': b'b', b'c': [b'd', b'e']}

        data = b'\xff\xff' + frame_bytes + b'\xff\xff\xff\xff\xff\xff\xff\xff'
        if frametype is SYNStreamFrame:
            data += b'\xff\xff\xff\xff\xff\xff\xff\xff'

        data += compressed

        fr, consumed = from_bytes(data, decobj)
        assert consumed == 0xFFFFFF + 8
        assert isinstance(fr, frametype)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set([FLAG_FIN, FLAG_UNIDIRECTIONAL])
        assert fr.stream_id == 0x7FFFFFFF
        assert fr.headers == nv_expected

        if frametype is SYNStreamFrame:
            assert fr.assoc_stream_id == 0x7FFFFFFF
            assert fr.priority == 0x07

    def test_syn_stream_frame_good(self):
        self.__test_syn_xxx_frame_good(b'\x00\x01', SYNStreamFrame)

    def test_syn_reply_frame_good(self):
        self.__test_syn_xxx_frame_good(b'\x00\x02', SYNReplyFrame)

    def test_rst_stream_frame_good(self):
        data = b'\xff\xff\x00\x03\x00\x00\x00\x08\xff\xff\xff\xff\x00\x00\x00\x01'
        fr, consumed = from_bytes(data)

        assert consumed == 16
        assert isinstance(fr, RSTStreamFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set()
        assert fr.stream_id == 0x7FFFFFFF
        assert fr.status_code == 1

    def test_settings_frame_good(self):
        data = b'\xff\xff\x00\x04\x01\x00\x00\x0c\x00\x00\x00\x01\x03\x00\x00\x01\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)

        assert consumed == 20
        assert isinstance(fr, SettingsFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set([FLAG_CLEAR_SETTINGS])
        assert len(fr.settings) == 1
        assert fr.settings[0].id == SETTINGS_UPLOAD_BANDWIDTH
        assert fr.settings[0].value == 0xFFFFFFFF
        assert fr.settings[0].flags == set([FLAG_SETTINGS_PERSIST_VALUE,
                                            FLAG_SETTINGS_PERSISTED])

    def test_ping_frame_good(self):
        data = b'\xff\xff\x00\x06\x00\x00\x00\x04\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)

        assert consumed == 12
        assert isinstance(fr, PingFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set()
        assert fr.ping_id == 0xFFFFFFFF

    def test_goaway_frame_good(self):
        data = b'\xff\xff\x00\x07\x00\x00\x00\x08\xff\xff\xff\xff\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)

        assert consumed == 16
        assert isinstance(fr, GoAwayFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set()
        assert fr.last_good_stream_id == 0x7FFFFFFF
        assert fr.status_code == 0xFFFFFFFF

    def test_headers_frame_good(self):
        # Prepare for the NV block.
        indata = b'\x00\x00\x00\x02\x00\x00\x00\x01a\x00\x00\x00\x01b\x00\x00\x00\x01c\x00\x00\x00\x03d\x00e'
        compobj = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        compressed = compobj.compress(indata)
        compressed += compobj.flush(zlib.Z_SYNC_FLUSH)
        decobj = zlib.decompressobj(zdict=SPDY_3_ZLIB_DICT)
        nv_expected = {b'a': b'b', b'c': [b'd', b'e']}

        data = (b'\xff\xff\x00\x08\x01\x00\x00' + chr(len(compressed) + 4).encode('ascii') + b'\xff\xff\xff\xff' + compressed)
        fr, consumed = from_bytes(data, decobj)

        assert consumed == 8 + 4 + len(compressed)
        assert isinstance(fr, HeadersFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set([FLAG_FIN])
        assert fr.stream_id == 0x7FFFFFFF
        assert fr.headers == nv_expected

    def test_window_update_frame_good(self):
        data = b'\xff\xff\x00\x09\x00\x00\x00\x08\xff\xff\xff\xff\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)

        assert consumed == 16
        assert isinstance(fr, WindowUpdateFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set()
        assert fr.stream_id == 0x7FFFFFFF
        assert fr.delta_window_size == 0x7FFFFFFF


class TestNVBlock(object):
    def test_basic_nv_block_parsing(self):
        indata = b'\x00\x00\x00\x02\x00\x00\x00\x01a\x00\x00\x00\x01b\x00\x00\x00\x01c\x00\x00\x00\x03d\x00e'
        compobj = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        compressed = compobj.compress(indata)
        compressed += compobj.flush(zlib.Z_SYNC_FLUSH)
        decobj = zlib.decompressobj(zdict=SPDY_3_ZLIB_DICT)
        expected = {b'a': b'b', b'c': [b'd', b'e']}

        headers = parse_nv_block(decobj, compressed)
        assert headers == expected

    def test_can_build_nv_block(self):
        indata = {b'a': b'b', b'c': [b'd', b'e']}
        compobj = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        decobj = zlib.decompressobj(zdict=SPDY_3_ZLIB_DICT)
        expected = b'\x00\x00\x00\x02\x00\x00\x00\x01a\x00\x00\x00\x01b\x00\x00\x00\x01c\x00\x00\x00\x03d\x00e'

        block = build_nv_block(compobj, indata)
        dec = decobj.decompress(block)
        assert dec == expected


class SYNStreamFrameCommon(object):
    def test_build_flags_all_flags(self):
        expected = set([FLAG_FIN, FLAG_UNIDIRECTIONAL])

        fr = self.frametype()
        fr.build_flags(0xFF)

        assert fr.flags == expected

    def test_build_flags_no_flags(self):
        expected = set()

        fr = self.frametype()
        fr.build_flags(0)

        assert fr.flags == expected


class TestSYNStreamFrame(SYNStreamFrameCommon):
    def setup(self):
        self.frametype = SYNStreamFrame

    def test_non_nv_block_data_good(self):
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'

        fr = self.frametype()
        fr.build_data(data, NullDecompressor())

        assert fr.stream_id == 0x7FFFFFFF
        assert fr.assoc_stream_id == 0x7FFFFFFF
        assert fr.priority == 0x07

    def test_can_build(self):
        expected = b'\x80\x03\x00\x01\x03\x00\x00\x20\x7f\xff\xff\xff\x7f\xff\xff\xff\x20\x00\x00\x00x\xbb\xe3\xc6\xa7\xc2\x02\xa6\x23\x46\x10\x06\x25\x6c\xc6\x24\x00\x00\x00\x00\xff\xff'
        compressor = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        fr = SYNStreamFrame()
        fr.version = 3
        fr.flags = set([FLAG_FIN, FLAG_UNIDIRECTIONAL])
        fr.stream_id = 0x7FFFFFFF
        fr.assoc_stream_id = 0x7FFFFFFF
        fr.priority = 1
        fr.headers = {b'a': b'b'}

        dumped = fr.to_bytes(compressor)
        assert dumped == expected


class TestSYNReplyFrame(SYNStreamFrameCommon):
    def setup(self):
        self.frametype = SYNReplyFrame

    def test_non_nv_block_data_good(self):
        data = b'\xff\xff\xff\xff'

        fr = self.frametype()
        fr.build_data(data, NullDecompressor())

        assert fr.stream_id == 0x7FFFFFFF

    def test_can_build(self):
        expected = b'\x80\x03\x00\x02\x01\x00\x00\x1a\x7f\xff\xff\xff\x78\xbb\xe3\xc6\xa7\xc2\x02\xa6\x23\x46\x10\x06\x25\x6c\xc6\x24\x00\x00\x00\x00\xff\xff'
        compressor = zlib.compressobj(zdict=SPDY_3_ZLIB_DICT)
        fr = SYNReplyFrame()
        fr.version = 3
        fr.flags = set([FLAG_FIN, FLAG_UNIDIRECTIONAL])
        fr.stream_id = 0x7FFFFFFF
        fr.assoc_stream_id = 0x7FFFFFFF
        fr.priority = 1
        fr.headers = {b'a': b'b'}

        dumped = fr.to_bytes(compressor)
        assert dumped == expected


class TestRSTStreamFrame(object):
    def test_build_flags_all_flags(self):
        fr = RSTStreamFrame()

        with raises(ValueError):
            fr.build_flags(0xFF)

    def test_build_flags_no_flags(self):
        expected = set()

        fr = RSTStreamFrame()
        fr.build_flags(0)

        assert fr.flags == expected

    def test_build_data_good(self):
        data = b'\xff\xff\xff\xff\x00\x00\x00\x01'

        fr = RSTStreamFrame()
        fr.build_data(data)

        assert fr.stream_id == 0x7FFFFFFF
        assert fr.status_code == PROTOCOL_ERROR

    def test_build_data_invalid_code(self):
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff'

        fr = RSTStreamFrame()

        with raises(RuntimeError):
            fr.build_data(data)

    def test_can_serialize(self):
        data = b'\x80\x03\x00\x03\x00\x00\x00\x08\x7f\xff\xff\xff\x00\x00\x00\x01'

        fr = RSTStreamFrame()
        fr.version = 3
        fr.stream_id = 0x7FFFFFFF
        fr.status_code = PROTOCOL_ERROR

        dumped = fr.to_bytes()
        assert dumped == data


class TestSettingsFrame(object):
    def test_build_flags_all_flags(self):
        expected = set([FLAG_CLEAR_SETTINGS])

        fr = SettingsFrame()
        fr.build_flags(0xFF)

        assert fr.flags == expected

    def test_build_flags_no_flags(self):
        expected = set()

        fr = SettingsFrame()
        fr.build_flags(0x00)

        assert fr.flags == expected

    def test_build_data_no_settings(self):
        data = b'\x00\x00\x00\x00'

        fr = SettingsFrame()
        fr.build_data(data)

        assert len(fr.settings) == 0

    def test_build_data_some_settings(self):
        data = b'\x00\x00\x00\x02\x01\x00\x00\x01\x00\x00\x00\x00\x02\x00\x00\x02\x00\x00\x00\x00'

        fr = SettingsFrame()
        fr.build_data(data)

        assert len(fr.settings) == 2
        assert fr.settings[0].id == 0x000001
        assert fr.settings[0].value == 0x00000000
        assert fr.settings[0].flags == set([FLAG_SETTINGS_PERSIST_VALUE])
        assert fr.settings[1].id == 0x000002
        assert fr.settings[1].value == 0x00000000
        assert fr.settings[1].flags == set([FLAG_SETTINGS_PERSISTED])


class TestPingFrame(object):
    def test_build_flags_all_flags(self):
        fr = PingFrame()

        with raises(ValueError):
            fr.build_flags(0xFF)

    def test_build_flags_no_flags(self):
        expected = set()

        fr = PingFrame()
        fr.build_flags(0x00)

        assert fr.flags == expected

    def test_build_data(self):
        data = b'\x00\x00\x00\x01'

        fr = PingFrame()
        fr.build_data(data)

        assert fr.ping_id == 1


class TestGoAwayFrame(object):
    def test_build_flags_all_flags(self):
        fr = GoAwayFrame()

        with raises(ValueError):
            fr.build_flags(0x0F)

    def test_build_flags_no_flags(self):
        expected = set()

        fr = GoAwayFrame()
        fr.build_flags(0x00)

        assert fr.flags == expected

    def test_build_data_good(self):
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff'

        fr = GoAwayFrame()
        fr.build_data(data)

        assert fr.last_good_stream_id == 0x7FFFFFFF
        assert fr.status_code == 0xFFFFFFFF


class TestHeaderFrame(object):
    def test_build_flags_all_flags(self):
        expected = set([FLAG_FIN])

        fr = HeadersFrame()
        fr.build_flags(0xFF)

        assert fr.flags == expected

    def test_build_flags_no_flags(self):
        expected = set()

        fr = HeadersFrame()
        fr.build_flags(0x00)

        assert fr.flags == expected

    def test_build_data_no_nv_block(self):
        data = b'\xff\xff\xff\xff\x00\x00\x00\x00'

        fr = HeadersFrame()
        fr.build_data(data, NullDecompressor())

        assert fr.stream_id == 0x7FFFFFFF


class TestWindowUpdateFrame(object):
    def test_build_flags_all_flags(self):
        fr = WindowUpdateFrame()

        with raises(ValueError):
            fr.build_flags(0xFF)

    def test_build_flags_no_flags(self):
        expected = set()

        fr = WindowUpdateFrame()
        fr.build_flags(0x00)

        assert fr.flags == expected

    def test_build_data_good(self):
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff'

        fr = WindowUpdateFrame()
        fr.build_data(data)

        assert fr.stream_id == 0x7FFFFFFF
        assert fr.delta_window_size == 0x7FFFFFFF
