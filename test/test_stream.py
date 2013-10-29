# -*- coding: utf-8 -*-
"""
test/test_stream
~~~~~~~~~~~~~~~~

Tests for the SPDY Stream abstraction.
"""
from spdypy.stream import *


class TestStream(object):
    def test_streams_require_stream_ids(self):
        s = Stream(1, None, None, None)
        assert s.stream_id == 1

    def test_streams_require_versions(self):
        s = Stream(None, 1, None, None)
        assert s.version == 1
