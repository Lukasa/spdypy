# -*- coding: utf-8 -*-
"""
test/test_frame
~~~~~~~~~~~~~~~
Tests of the SPDY frame.
"""
from spdypy.frame import (Frame, SYNStreamFrame, flags, SYN_STREAM, SYN_REPLY,
                          RST_STREAM, SETTINGS, PING, GOAWAY, HEADERS,
                          WINDOW_UPDATE, FLAG_FIN, FLAG_UNIDIRECTIONAL,
                          FLAG_CLEAR_SETTINGS)
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
            assert result == flags(0xFF, frame_type)


class TestSYNStreamFrame(object):
    def test_build_flags_all_flags(self):
        expected = set([FLAG_FIN, FLAG_UNIDIRECTIONAL])

        fr = SYNStreamFrame()
        fr.build_flags(0xFF)

        assert fr.flags == expected

    def test_build_flags_no_flags(self):
        expected = set()

        fr = SYNStreamFrame()
        fr.build_flags(0)

        assert fr.flags == expected
