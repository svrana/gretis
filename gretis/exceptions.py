from redis.exceptions import RedisError


class ConnectionInvalidContext(RedisError):
    pass
