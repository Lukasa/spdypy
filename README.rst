SPDYPy: SPDY for Lovers
=======================

SPDYPy (pronounced like *sweetie-pie*) is a library for easily making and
working with SPDY connections, written in pure Python, depending on nothing but
the standard library.

Protocols like `SPDY <https://en.wikipedia.org/wiki/SPDY>`_ have the potential
to dramatically improve the efficiency of HTTP transport on the world wide web.
But for that to happen it needs to be easy for application developers to
transition into using SPDY, without requiring tedious and painful rewriting of
their code. SPDYPy's goal is to make this easy. Take a look:

.. code-block:: pycon

    >>> conn = SPDYConnection('www.google.com')
    >>> conn.request('GET', '/')
    >>> resp = conn.getresponse()
    >>> resp.status
    200
    >>> resp.read()
    b'...'

Note
----

SPDYPy is currently under active development. This means that the API is in
flux, features may or may not be implemented, and I may go long periods of time
without making improvements. Using this library in its current state is at your
own risk: be warned.

(Planned) Features
------------------

*Features that have been implemented are in bold.*

- Stream Management
- Server Push Support
- Fully synchronous API, ready for insertion into your concurrency framework of
  choice.
- SSL certificate verification.
- HTTPS connection fallback for non-SPDY connections.
- Hopefully many more.

Support
-------

SPDYPy currently only supports Python 3.3+, because that is the earliest
version of Python that supports TLS Next Protocol Negotation. If anyone is
able to backport that support into earlier versions, please get in touch.

For the same reason, SPDYPy also requires OpenSSL version 1.0.1 or later,
because that is the minimum version that supports NPN. If your currently
installed version of OpenSSL is older than that you will need to upgrade, and
then recompile Python 3.3 against the new version of OpenSSL.

Instructions for how to do this will come shortly.

License
-------

SPDYPy is licensed under the MIT License. See LICENSE for details.

Maintainer
----------

SPDYPy was created and is maintained by
`Cory Benfield <https://lukasa.co.uk/>`_.
