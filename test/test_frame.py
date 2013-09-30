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

    def test_frame_default_field_values(self):
        fr = Frame()
        assert fr.control is None
        assert fr.version is None
        assert fr.type is None
        assert fr.flags == []
        assert fr.data is None
