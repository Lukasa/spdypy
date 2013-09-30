# -*- coding: utf-8 -*-
"""
test/test_api
~~~~~~~~~

Tests of the top-level SPDYPy API. These will be relatively sparse for the
moment.
"""
# Nasty little path hack.
import sys
sys.path.append('.')


class TestAPI(object):
    """
    Tests for the top-level spdypy API.
    """
    def test_can_import_spdypy_on_py_33(self):
        import spdypy
        assert True
