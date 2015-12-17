gretis
==========

An asynchronous redis::Connection object using Greenlets and Tornado's
event-loop.

Installation
------------

To install gretis, simply:

.. code-block:: bash

    $ sudo pip install gretis

or alternatively (you really should be using pip though):

.. code-block:: bash

    $ sudo easy_install gretis

or from source:

.. code-block:: bash

    $ sudo python setup.py install


Getting Started
---------------

With redis-py:

Create a redis ConnectionPool instructing it to use the Gredis
AsyncConnection as its connection.


.. code-block:: pycon

    >>> import redis
    >>> from gretis.async_connection import AsyncConnection
    >>>
    >>> pool = redis.ConnectionPool(connection_class=AsyncConnection,
                                    host='localhost', port=6379, db=0,
                                    socket_timeout=1)
    >>> r = redis.StrictRedis(connection_pool=pool)
    >>> r.set('foo', 'bar')
    True
    >>> r.get('foo')
    'bar'

Or with redis-cluster-py:

Create a redis cluster ConnectionPool and give it an AsyncClusterConnection.


.. code-block:: pycon

    >>> import redis
    >>> from gretis.async_cluster_connection import AsyncClusterConnection
    >>> from rediscluster import ClusterConnectionPool, StrictClusterRedis
    >>>
    >>> pool = ClusterConnectionPool(connection_class=AsyncClusterConnection,
                                     host='localhost', port=700,
                                     socket_timeout=1)
    >>> r = StrictRedisCluster(connection_pool=pool,
                               max_connections=2**31,
                               socket_timeout=1)
    >>> r.set('foo', 'bar')
    True
    >>> r.get('foo')
    'bar'

