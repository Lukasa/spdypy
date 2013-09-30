# -*- coding: utf-8 -*-
"""
spdypy.connection
~~~~~~~~~~~~~~~~~

Contains the code necessary for working with SPDY connections.
"""


class SPDYConnection(object):
    """
    A representation of a single SPDY connection to a remote server. This
    object takes responsibility for managing the complexities of the SPDY
    protocol, including streams and options. This complexity is abstracted
    away into an interface that broadly looks like the standard library's
    HTTPSConnection class.

    :param host: The host to establish a connection to.
    """
    def __init__(self, host):
        self.host = host
        self._state = None
