# -*- coding: utf-8 -*-
"""
A basic example of how to use SPDY.

This example is currently incomplete, but should remain current to the state of
the library. This means that it enumerates the full state of everything
SPDYPy can do.
"""
import sys
sys.path.append('.')
import spdypy

conn = spdypy.SPDYConnection('www.google.com')
conn.putrequest('GET', '/')
conn.putheader('user-agent', 'spdypy')
conn.putheader('accept', '*/*')
conn.putheader('accept-encoding', 'gzip,deflate')
conn.endheaders()

# Debugging output for now.
frame_list = conn._read_outstanding(timeout=0.5)
while frame_list:
    for frame in frame_list:
        print(frame)

    frame_list = conn._read_outstanding(timeout=0.5)
