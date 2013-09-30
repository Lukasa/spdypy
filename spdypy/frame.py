# -*- coding: utf-8 -*-
"""
spdypy.frame
~~~~~~~~~~~~

Defines SPDYPy's internal representation of a SPDY frame.
"""


class Frame(object):
    """
    A single SPDY frame.
    """
    def __init__(self):
        self.control = None
        self.version = None
        self.type = None
        self.flags = []
        self.data = None
        self.stream_id = None
