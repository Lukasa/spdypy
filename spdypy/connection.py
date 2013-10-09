# -*- coding: utf-8 -*-
"""
spdypy.connection
~~~~~~~~~~~~~~~~~

Contains the code necessary for working with SPDY connections.
"""
# Define some states for SPDYConnections.
NEW = 'NEW'


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
        self._state = NEW

    def request(self, method, url, body=None, headers={}):
        """
        This will send a request to the server using the HTTP request method
        ``method`` and the selector ``url``. If the ``body`` argument is
        present, it should be a string or bytes object of data to send after
        the headers are finished. Strings are encoded as ISO-8859-1, the
        default charset for HTTP. To use other encodings, pass a bytes object.
        The Content-Length header is set to the length of the string.

        The ``headers`` object should be a mapping of extra HTTP headers to
        send with the request.
        """
        pass
