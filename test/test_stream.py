# -*- coding: utf-8 -*-
"""
test/test_stream
~~~~~~~~~~~~~~~~

Tests for the SPDY Stream abstraction.
"""
from spdypy.stream import *
from .test_frame import NullCompressor

class MockConnection(object):
    """
    A useful test object that keeps a buffer of data, and a record of how many
    times it was called.
    """
    def __init__(self):
        self.buffer = b''
        self.called = 0

    def send(self, data):
        self.buffer += data
        self.called += 1


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

    def test_we_can_correctly_end_a_stream(self):
        s = Stream(5, 3, None, None)
        s.open_stream(priority=1)

        # Confirm that FLAG_FIN is set on the first frame.
        assert FLAG_FIN in s._queued_frames[0].flags

        s.prepare_data(b'TestTestTest', last=True)

        # Confirm that FLAG_FIN is now on the last frame, not the first.
        frame = s._next_frame()
        assert FLAG_FIN not in frame.flags

        frame = s._next_frame()
        assert FLAG_FIN in frame.flags

    def test_streams_serialize_frame_by_frame(self):
        s = Stream(5, 3, NullCompressor(), None)
        conn = MockConnection()

        s.open_stream(priority=1)
        s.prepare_data(b'TestTestTest', last=True)

        # 'send' the data.
        s.send_outstanding(conn)

        assert conn.called == 2

    def test_streams_empty_frame_buffer_after_sending(self):
        s = Stream(5, 3, NullCompressor(), None)
        conn = MockConnection()

        s.open_stream(priority=1)
        s.prepare_data(b'TestTestTest', last=True)
        s.send_outstanding(conn)

        assert len(s._queued_frames) == 0
