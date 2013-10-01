# -*- coding: utf-8 -*-
"""
test/test_frame
~~~~~~~~~~~~~~~
Tests of the SPDY frame.
"""
from spdypy.frame import (Frame, flags, SYN_STREAM, SYN_REPLY, RST_STREAM,
                          SETTINGS, PING, GOAWAY, HEADERS, WINDOW_UPDATE,
                          FLAG_FIN, FLAG_UNIDIRECTIONAL, FLAG_CLEAR_SETTINGS)


class TestFrame(object):
    def test_can_create_blank_frame(self):
        assert Frame()

    def test_frame_default_field_values(self):
        fr = Frame()
        assert fr.control is None
        assert fr.version is None
        assert fr.type is None
        assert fr.flags == []
        assert fr.data is None
        assert fr.stream_id is None

class TestFlags(object):
    def test_all_flags_set(self):
        # This test isn't totally realistic, as the server shouldn't set
        # undefined flags, but it's a good test of output.
        expected = {SYN_STREAM: [FLAG_FIN, FLAG_UNIDIRECTIONAL],
                    SYN_REPLY: [FLAG_FIN],
                    RST_STREAM: [],
                    SETTINGS: [FLAG_CLEAR_SETTINGS],
                    PING: [],
                    GOAWAY: [],
                    HEADERS: [FLAG_FIN],
                    WINDOW_UPDATE: []}

        for frame_type, result in expected.items():
            assert result == flags(0xFF, frame_type)
