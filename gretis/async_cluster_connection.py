from rediscluster.connection import (
    ClusterParser,
)

from .async_connection import (
    AsyncConnection,
    AsyncSSLConnection,
)


class AsyncClusterConnection(AsyncConnection):
    description_format = ("AsyncClusterConnection"
                          "<host=%(host)s,port=%(port)s>")

    def __init__(self, *args, **kwargs):
        kwargs['parser_class'] = ClusterParser
        super(AsyncClusterConnection, self).__init__(*args, **kwargs)


class AsyncClusterSSLConnection(AsyncSSLConnection):
    description_format = ("AsyncClusterSSLConnection"
                          "<host=%(host)s,port=%(port)s>")

    def __init__(self, *args, **kwargs):
        kwargs['parser_class'] = ClusterParser
        super(AsyncClusterSSLConnection, self).__init__(*args, **kwargs)
