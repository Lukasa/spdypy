# -*- coding: utf-8 -*-
"""
test/test_connection
~~~~~~~~~~~~~~~~~~~~~

Tests for the SPDYConnection object.
"""
import spdypy
import spdypy.connection


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
