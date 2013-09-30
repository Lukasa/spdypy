# -*- coding: utf-8 -*-
"""
test/test_frame
~~~~~~~~~~~~~~~
Tests of the SPDY frame.
"""
from spdypy.frame import Frame


class TestFrame(object):
    def test_can_create_blank_frame(self):
        assert Frame()
