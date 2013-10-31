# -*- coding: utf-8 -*-
"""
test/test_stream
~~~~~~~~~~~~~~~~

Tests for the SPDY Stream abstraction.
"""
from spdypy.stream import *
from spdypy.stream import SYNStreamFrame, DataFrame


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

    def test_associating_streams(self):
        s = Stream(5, 3, None, None)
        assoc = Stream(2, 3, None, None)
        s.open_stream(priority=1, associated_stream=assoc)

        # Confirm that the first frame has the correct associated stream ID.
        frame = s._next_frame()

        assert frame.assoc_stream_id == 2

    def test_stream_priority_is_preserved(self):
        s = Stream(5, 3, None, None)
        s.open_stream(priority=1)

        frame = s._next_frame()
        assert frame.priority == 1

    def test_open_stream_with_headers(self):
        s = Stream(5, 3, None, None)
        s.open_stream(priority=1)
        s.add_header(b'Key', b'Value')
        s.add_header(b'Key2', b'Value2')

        frame = s._next_frame()
        expected = {b'Key': b'Value', b'Key2': b'Value2'}
        assert frame.headers == expected

    def test_we_can_add_data(self):
        s = Stream(5, 3, None, None)
        s.open_stream(priority=1)
        s.prepare_data(b'TestTestTest')

        _ = s._next_frame()
        frame = s._next_frame()

        assert isinstance(frame, DataFrame)
        assert frame.data == b'TestTestTest'
