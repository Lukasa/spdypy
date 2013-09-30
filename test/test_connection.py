# -*- coding: utf-8 -*-
"""
tests/test_connection
~~~~~~~~~~~~~~~~~~~~~

Tests for the SPDYConnection object.
"""
import spdypy


class TestSPDYConnection(object):
    def test_can_create_connection(self):
        conn = spdypy.SPDYConnection(None)


class TestSPDYConnectionState(object):
    def test_connection_has_state(self):
        conn = spdypy.SPDYConnection(None)
        assert hasattr(conn, '_state')
