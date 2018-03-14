# gretis

An asynchronous redis::Connection object using Greenlets and Tornado's event-loop.

## Requires

  * [Tornado](https://github.com/tornadoweb/tornado)
  * [Greenlet](https://github.com/python-greenlet/greenlet)

## Installation

```bash
   pip install gretis
```

## Getting Started

With redis-py:

Create a redis ConnectionPool instructing it to use the Gretis AsyncConnection
as its connection. You must have a parent greenlet or you will get an
exception. (Examples assume you are in greenlet context already)


```python

import redis
from gretis.async_connection import AsyncConnection

pool = redis.ConnectionPool(connection_class=AsyncConnection,
    host='localhost', port=6379, db=0, socket_timeout=1)
r = redis.StrictRedis(connection_pool=pool)
r.set('foo', 'bar')

```

Or with redis-cluster-py:

Create a redis cluster ConnectionPool and give it an AsyncClusterConnection.

```python

import redis
from gretis.async_cluster_connection import AsyncClusterConnection
from rediscluster import ClusterConnectionPool, StrictClusterRedis

pool = ClusterConnectionPool(connection_class=AsyncClusterConnection,
    host='localhost', port=700, socket_timeout=1)
r = StrictRedisCluster(connection_pool=pool)
r.set('foo', 'bar')
```
