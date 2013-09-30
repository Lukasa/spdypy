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
