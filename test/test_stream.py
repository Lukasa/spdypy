# -*- coding: utf-8 -*-
"""
test/test_stream
~~~~~~~~~~~~~~~~

Tests for the SPDY Stream abstraction.
"""
from spdypy.stream import *


class TestStream(object):
    def test_streams_require_stream_ids(self):
        s = Stream(1)
        assert s.stream_id == 1
