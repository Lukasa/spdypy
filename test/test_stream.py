# -*- coding: utf-8 -*-
"""
test/test_stream
~~~~~~~~~~~~~~~~

Tests for the SPDY Stream abstraction.
"""
from spdypy.stream import *
from spdypy.stream import SYNStreamFrame


class TestStream(object):
    def test_streams_require_stream_ids(self):
        s = Stream(1, None, None, None)
        assert s.stream_id == 1

    def test_streams_require_versions(self):
        s = Stream(None, 1, None, None)
        assert s.version == 1

    def test_simple_stream_with_no_body_data(self):
        s = Stream(5, 3, None, None)
        s.open_stream(priority=1)

        # There should be only one frame, with no headers.
        frame = s._next_frame()

        assert isinstance(frame, SYNStreamFrame)
        assert frame.headers == {}

        assert s._next_frame() is None
