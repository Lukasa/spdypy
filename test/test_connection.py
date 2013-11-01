# -*- coding: utf-8 -*-
"""
test/test_connection
~~~~~~~~~~~~~~~~~~~~~

Tests for the SPDYConnection object.
"""
import spdypy
import spdypy.connection
from .test_stream import MockConnection


class TestSPDYConnection(object):
    def test_can_create_connection(self):
        conn = spdypy.SPDYConnection(None)
        assert conn


class TestSPDYConnectionState(object):
    def test_connection_has_state(self):
        conn = spdypy.SPDYConnection(None)
        assert hasattr(conn, '_state')

    def test_initial_connection_state_is_new(self):
        conn = spdypy.SPDYConnection(None)
        assert conn._state == spdypy.connection.NEW

    def test_new_streams_use_new_stream_id(self):
        conn = spdypy.SPDYConnection('www.google.com')
        conn._sck = MockConnection()
        stream_id = conn.putrequest(b'GET', b'/')

        assert len(conn._streams) == 1
        assert stream_id == 1
        assert conn._streams[stream_id]

        second_stream_id = conn.putrequest(b'POST', b'other')

        assert len(conn._streams) == 2
        assert second_stream_id == 3
        assert conn._streams[second_stream_id]

    def test_spec_mandatory_headers_are_present(self):
        conn = spdypy.SPDYConnection('www.google.com')
        conn._sck = MockConnection()
        stream_id = conn.putrequest(b'GET', b'/')

        mandatory_headers = {
            b':method': b'GET',
            b':path': b'/',
            b':version': b'HTTP/1.1',
            b':host': b'www.google.com',
            b':scheme': b'https'
        }

        stream = conn._streams[stream_id]

        # We probably need a better way to test this than reaching the whole
        # way through the stack.
        assert stream._queued_frames[0].headers == mandatory_headers

    def test_putheader_can_add_headers(self):
        conn = spdypy.SPDYConnection('www.google.com')
        conn._sck = MockConnection()
        stream_id = conn.putrequest(b'GET', b'/')
        conn.putheader(b'Key', b'Value')

        headers = {
            b':method': b'GET',
            b':path': b'/',
            b':version': b'HTTP/1.1',
            b':host': b'www.google.com',
            b':scheme': b'https',
            b'Key': b'Value',
        }

        stream = conn._streams[stream_id]

        assert stream._queued_frames[0].headers == headers

    def test_putheader_does_most_recent_stream_by_default(self):
        conn = spdypy.SPDYConnection('www.google.com')
        conn._sck = MockConnection()
        stream_id = conn.putrequest(b'GET', b'/')
        stream_id2 = conn.putrequest(b'POST', b'/post')

        conn.putheader(b'Key', b'Value')

        headers = {
            b':method': b'POST',
            b':path': b'/post',
            b':version': b'HTTP/1.1',
            b':host': b'www.google.com',
            b':scheme': b'https',
            b'Key': b'Value',
        }

        first_stream = conn._streams[stream_id]
        second_stream = conn._streams[stream_id2]

        assert first_stream._queued_frames[0].headers != headers
        assert second_stream._queued_frames[0].headers == headers

    def test_can_specify_stream_for_headers(self):
        conn = spdypy.SPDYConnection('www.google.com')
        conn._sck = MockConnection()
        stream_id = conn.putrequest(b'GET', b'/')
        stream_id2 = conn.putrequest(b'POST', b'/post')

        conn.putheader(b'Key', b'Value', stream_id=stream_id)

        headers = {
            b':method': b'GET',
            b':path': b'/',
            b':version': b'HTTP/1.1',
            b':host': b'www.google.com',
            b':scheme': b'https',
            b'Key': b'Value',
        }

        first_stream = conn._streams[stream_id]
        second_stream = conn._streams[stream_id2]

        assert first_stream._queued_frames[0].headers == headers
        assert second_stream._queued_frames[0].headers != headers

    def test_endheaders_sends_outstanding_data(self):
        conn = spdypy.SPDYConnection('www.google.com')
        mock = MockConnection()
        conn._sck = mock
        conn.putrequest(b'GET', b'/')
        conn.endheaders()

        assert mock.called == 1

    def test_endheaders_can_add_data(self):
        conn = spdypy.SPDYConnection('www.google.com')
        mock = MockConnection()
        conn._sck = mock
        conn.putrequest(b'GET', b'/')
        conn.endheaders(message_body=b'TestTestTest')

        assert mock.called == 2
        assert mock.buffer.endswith(b'TestTestTest')
