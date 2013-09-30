# -*- coding: utf-8 -*-
"""
spdypy - SPDY for lovers
~~~~~~~~~~~~~~~~~~~~~~~~

SPDYPy is a library for easily making and working with SPDY connections,
written in pure Python, depending on nothing but the standard library.

:copyright: (c) 2013 by Cory Benfield.
:license: MIT, see LICENSE for details.
"""

__title__ = 'spdypy'
__version__ = '0.0.0'
__build__ = 0x000000
__author__ = 'Cory Benfield'
__license__ = 'MIT'
__copyright__ = 'Copyright 2013 Cory Benfield'

# Python version check.
import sys

version = sys.version_info

if version[0] == 2 or version[1] < 3:
    raise ImportError("Minimum Python version is 3.3.")

from .connection import SPDYConnection
