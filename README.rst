gretis
==========

An asyncronous redis::Connection object using Greenlets and Tornado's
event-loop.

Installation
------------

To install gretis, simply:

.. code-block:: bash

    $ sudo pip install gretis

or alternatively (you really should be using pip though):

.. code-block:: bash

    $ sudo easy_install greenredis

or from source:

.. code-block:: bash

    $ sudo python setup.py install


Getting Started
---------------

Create a redis ConnectionPool instructing it to use the Greenredis
AsyncConnection as its connection.


.. code-block:: pycon

    >>> import redis
    >>> import gretis
    >>>
    >>> pool = redis.ConnectionPool(host='localhost', port=6379, db=0,
                                    socket_timeout=1)
    >>> r = redis.StrictRedis(connection_pool=pool)
    >>> r.set('foo', 'bar')
    True
    >>> r.get('foo')
    'bar'
