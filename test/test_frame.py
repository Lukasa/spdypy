# -*- coding: utf-8 -*-
"""
test/test_frame
~~~~~~~~~~~~~~~
Tests of the SPDY frame.
"""
from spdypy.frame import *
from pytest import raises


class TestFrame(object):
    def test_can_create_blank_frame(self):
        assert Frame()

    def test_frame_default_field_values(self):
        fr = Frame()
        assert fr.control is None
        assert fr.version is None
        assert fr.type is None
        assert fr.flags == set()
        assert fr.data is None
        assert fr.stream_id is None

    def test_frame_is_abc(self):
        fr = Frame()

        with raises(NotImplementedError):
            fr.build_flags(0x00)

        with raises(NotImplementedError):
            fr.build_data('')


class TestFlags(object):
    def test_all_flags_set(self):
        # This test isn't totally realistic, as the server shouldn't set
        # undefined flags, but it's a good test of output.
        expected = {SYN_STREAM: set([FLAG_FIN, FLAG_UNIDIRECTIONAL]),
                    SYN_REPLY: set([FLAG_FIN]),
                    RST_STREAM: set(),
                    SETTINGS: set([FLAG_CLEAR_SETTINGS]),
                    PING: set(),
                    GOAWAY: set(),
                    HEADERS: set([FLAG_FIN]),
                    WINDOW_UPDATE: set()}

        for frame_type, result in expected.items():
            assert result == parse_flags(0xFF, frame_type)


class TestFromBytes(object):
    def __test_syn_xxx_frame_good(self, frame_bytes, frametype):
        data = b'\xff\xff' + frame_bytes + b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)
        assert consumed == 0xFFFFFF + 8
        assert isinstance(fr, frametype)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set([FLAG_FIN, FLAG_UNIDIRECTIONAL])
        assert fr.stream_id == 0x7FFFFFFF
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
        data = b'\xff\xff\x00\x08\x01\x00\x00\x10\xff\xff\xff\xff\x00\x00\x00\x01\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)

        assert consumed == 24
        assert isinstance(fr, HeadersFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set([FLAG_FIN])
        assert fr.stream_id == 0x7FFFFFFF
        assert fr.name_value_block == b'\xff\xff\xff\xff'


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

    def test_non_nv_block_data_good(self):
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'

        fr = self.frametype()
        fr.build_data(data)

        assert fr.stream_id == 0x7FFFFFFF
        assert fr.assoc_stream_id == 0x7FFFFFFF
        assert fr.priority == 0x07


class TestSYNStreamFrame(SYNStreamFrameCommon):
    def setup(self):
        self.frametype = SYNStreamFrame


class TestSYNReplyFrame(SYNStreamFrameCommon):
    def setup(self):
        self.frametype = SYNReplyFrame


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
        assert fr.status_code == 1

    def test_build_data_invalid_code(self):
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff'

        fr = RSTStreamFrame()

        with raises(RuntimeError):
            fr.build_data(data)


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

    def test_build_data_good(self):
        data = b'\xff\xff\xff\xff\x00\x00\x00\x01\xff\xff\xff\xff'

        fr = HeadersFrame()
        fr.build_data(data)

        assert fr.stream_id == 0x7FFFFFFF
        assert fr.name_value_block == b'\xff\xff\xff\xff'


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
