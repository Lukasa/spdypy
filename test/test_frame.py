# -*- coding: utf-8 -*-
"""
test/test_frame
~~~~~~~~~~~~~~~
Tests of the SPDY frame.
"""
from spdypy.frame import (Frame, SYNStreamFrame, SYNReplyFrame, RSTStreamFrame,
                          SettingsFrame, parse_flags, from_bytes, SYN_STREAM,
                          SYN_REPLY, RST_STREAM, SETTINGS, PING, GOAWAY,
                          HEADERS, WINDOW_UPDATE, FLAG_FIN,
                          FLAG_UNIDIRECTIONAL, FLAG_CLEAR_SETTINGS,
                          FLAG_SETTINGS_PERSIST_VALUE, FLAG_SETTINGS_PERSISTED)
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
    def test_syn_stream_frame_good(self):
        data = b'\xff\xff\x00\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
        fr, consumed = from_bytes(data)
        assert consumed == 0xFFFFFF + 8
        assert isinstance(fr, SYNStreamFrame)
        assert fr.control
        assert fr.version == 0x7FFF
        assert fr.flags == set([FLAG_FIN, FLAG_UNIDIRECTIONAL])
        assert fr.stream_id == 0x7FFFFFFF
        assert fr.assoc_stream_id == 0x7FFFFFFF
        assert fr.priority == 0x07


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
        data = b'\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x00\x02\x00\x00\x02\x00\x00\x00\x00'

        fr = SettingsFrame()
        fr.build_data(data)

        assert len(fr.settings) == 2
        assert fr.settings[0][0] == 0x000001
        assert fr.settings[0][1] == 0x00000000
        assert fr.settings[0][2] == set([FLAG_SETTINGS_PERSIST_VALUE])
        assert fr.settings[1][0] == 0x000002
        assert fr.settings[1][1] == 0x00000000
        assert fr.settings[1][2] == set([FLAG_SETTINGS_PERSISTED])
