from __future__ import with_statement
import functools
import datetime
from select import select
import socket
import ssl
import uuid

import greenlet
from tornado.iostream import IOStream
from tornado.iostream import SSLIOStream
from tornado.ioloop import IOLoop

from redis._compat import iteritems
from redis.connection import (
    Connection,
    HiredisParser,
    HIREDIS_SUPPORTS_CALLABLE_ERRORS,
    SERVER_CLOSED_CONNECTION_ERROR,
)
from redis.exceptions import (
    RedisError,
    ConnectionError,
    TimeoutError,
    ResponseError,
)

from .exceptions import ConnectionInvalidContext

def generate_handle():
    return str(uuid.uuid4())


class AsyncHiredisParser(HiredisParser):
    def __init__(self, socket_read_size):
        self._ioloop = None
        self._iostream = None
        self._timeout_handle = None
        self._events = {}

        super(AsyncHiredisParser, self).__init__(socket_read_size)

    def on_disconnect(self):
        if self._iostream is None:
            return

        if self._timeout_handle:
            self._ioloop.remove_timeout(self._timeout_handle)
            self._timeout_handle = None
        self._iostream.set_close_callback(None)

        self._ioloop = None
        self._iostream = None

        super(AsyncHiredisParser, self).on_disconnect()

    def on_connect(self, connection):
        self._ioloop = connection._ioloop
        self._iostream = connection._iostream
        self._read_timeout = connection.socket_timeout

        super(AsyncHiredisParser, self).on_connect(connection)

    def _handle_read_timeout(self, read_greenlet):
        read_greenlet.throw(TimeoutError("Timeout reading from socket"))

    def _handle_read_error(self, read_greenlet, handle):
        """ Connection error, stream is closed """
        if handle in self._events and not read_greenlet.dead:
            read_greenlet.throw(ConnectionError("Timeout reading from socket"))

    def _handle_read_complete(self, read_greenlet, handle, data):
        if handle in self._events and not read_greenlet.dead:
            read_greenlet.switch(data)

    def read_response(self):
        if not self._reader:
            raise ConnectionError(SERVER_CLOSED_CONNECTION_ERROR)

        # _next_response might be cached from a can_read() call
        if self._next_response is not False:
            response = self._next_response
            self._next_response = False
            return response

        current = greenlet.getcurrent()
        parent = current.parent

        response = self._reader.gets()
        while response is False:
            handle = generate_handle()
            self._events[handle] = True
            self._iostream.set_close_callback(
                functools.partial(self._handle_read_error, current, handle)
            )

            if self._read_timeout:
                self._timeout_handle = self._ioloop.add_timeout(
                    datetime.timedelta(seconds=self._read_timeout),
                    functools.partial(self._handle_read_timeout, current)
                )
            self._iostream.read_bytes(
                self.socket_read_size,
                functools.partial(self._handle_read_complete, current, handle),
                partial=True
            )
            try:
                data = parent.switch()
            finally:
                if self._timeout_handle:
                    self._ioloop.remove_timeout(self._timeout_handle)
                    self._timeout_handle = None

                self._iostream.set_close_callback(None)
                del self._events[handle]

            # an empty string indicates the server shutdown the socket
            if not isinstance(data, bytes) or len(data) == 0:
                raise ConnectionError(SERVER_CLOSED_CONNECTION_ERROR)

            self._reader.feed(data)
            response = self._reader.gets()
        # if an older version of hiredis is installed, we need to attempt
        # to convert ResponseErrors to their appropriate types.
        if not HIREDIS_SUPPORTS_CALLABLE_ERRORS:
            if isinstance(response, ResponseError):
                response = self.parse_error(response.args[0])
            elif isinstance(response, list) and response and \
                    isinstance(response[0], ResponseError):
                response[0] = self.parse_error(response[0].args[0])
        # if the response is a ConnectionError or the response is a list and
        # the first item is a ConnectionError, raise it as something bad
        # happened
        if isinstance(response, ConnectionError):
            raise response
        elif isinstance(response, list) and response and \
                isinstance(response[0], ConnectionError):
            raise response[0]
        return response


class AsyncConnection(Connection):
    """
    Manages TCP communication to and from a Redis server
    """
    description_format = ("AsyncConnection"
                          "<host=%(host)s,port=%(port)s,db=%(db)s>")

    def __init__(self, *args, **kwargs):
        self._ioloop = kwargs.pop('ioloop', IOLoop.instance())
        kwargs['parser_class'] = kwargs.pop('parser_class', AsyncHiredisParser)
        super(AsyncConnection, self).__init__(*args, **kwargs)

        self._iostream = None
        self._timeout_handle = None
        self._events = {}

    def _wrap_socket(self, sock):
        return IOStream(sock)

    def _get_current_greenlet(self):
        if greenlet.getcurrent().parent is None:
            raise ConnectionInvalidContext("Greenlet parent not found, "
                                           "cannot perform async operations")
        return greenlet.getcurrent()

    def _handle_timeout(self, timeout_greenlet):
        timeout_greenlet.throw(ConnectionError('Connection timed out'))

    def _handle_error(self, error_greenlet, handle):
        """ Connection error, stream is closed """
        if handle in self._events and not error_greenlet.dead:
            error_greenlet.throw(ConnectionError('Error connecting to host'))

    def _handle_connect(self, connect_greenlet, handle):
        if handle in self._events and not connect_greenlet.dead:
            connect_greenlet.switch()

    def _connect(self):
        "Create a TCP socket connection"
        # we want to mimic what socket.create_connection does to support
        # ipv4/ipv6, but we want to set options prior to calling
        # socket.connect()
        if self._iostream:
            return

        current = self._get_current_greenlet()
        parent = current.parent

        err = None
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            family, socktype, proto, _, socket_address = res
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                # TCP_NODELAY
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                # TCP_KEEPALIVE
                if self.socket_keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in iteritems(self.socket_keepalive_options):
                        sock.setsockopt(socket.SOL_TCP, k, v)

                self._iostream = self._wrap_socket(sock)

                timeout = self.socket_connect_timeout
                if timeout:
                    self._timeout_handle = self._ioloop.add_timeout(
                        datetime.timedelta(seconds=timeout),
                        functools.partial(self._handle_timeout, current),
                    )

                handle = generate_handle()
                self._events[handle] = True
                self._iostream.set_close_callback(
                    functools.partial(self._handle_error, current, handle)
                )
                self._iostream.connect(
                    socket_address,
                    callback=functools.partial(self._handle_connect, current, handle)
                )

                # yield back to parent, wait for connect, error or timeout
                try:
                    parent.switch()
                finally:
                    if self._timeout_handle:
                        self._ioloop.remove_timeout(self._timeout_handle)
                        self._timeout_handle = None
                    self._iostream.set_close_callback(None)
                    del self._events[handle]
                return sock
            except ConnectionError as _:
                err = _
                if sock is not None:
                    sock.close()
                if self._iostream is not None:
                    self._iostream.close()
                    self._iostream = None

        if err is not None:
            raise err
        raise socket.error("socket.getaddrinfo returned an empty list")

    def disconnect(self):
        "Disconnects from the Redis server"
        if self._iostream is None:
            return

        if self._timeout_handle:
            self._ioloop.remove_timeout(self._timeout_handle)
            self._timeout_handle = None
        self._iostream.set_close_callback(None)
        self._iostream.close()
        self._iostream = None

        # This will call into the AsynchiredisParser on_disconnect.
        super(AsyncConnection, self).disconnect()

    def _handle_write_timeout(self, write_greenlet):
        write_greenlet.throw(TimeoutError("Timeout writing to socket"))

    def _handle_write_error(self, write_greenlet, handle):
        """ Connection error, stream is closed """
        if handle in self._events and not write_greenlet.dead:
            write_greenlet.throw(
                ConnectionError("Socket error during write")
            )

    def _handle_write_complete(self, write_greenlet, handle):
        if handle in self._events and not write_greenlet.dead:
            write_greenlet.switch()

    def send_packed_command(self, command):
        "Send an already packed command to the Redis server"
        current = self._get_current_greenlet()
        parent = current.parent

        if not self._iostream:
            self.connect()

        try:
            handle = datetime.datetime.now().strftime('%s')
            self._events[handle] = True

            if isinstance(command, str):
                command = [command]
            ncmds = len(command)
            for i, item in enumerate(command):
                if i == (ncmds-1):
                    cb = functools.partial(self._handle_write_complete, current, handle)
                    self._iostream.set_close_callback(
                        functools.partial(self._handle_write_error, current, handle)
                    )

                    self._timeout_handle = self._ioloop.add_timeout(
                        datetime.timedelta(seconds=self.socket_timeout),
                        functools.partial(self._handle_write_timeout, current)
                    )
                else:
                    cb = None

                self._iostream.write(item, callback=cb)

            try:
                parent.switch()
            finally:
                if self._timeout_handle:
                    self._ioloop.remove_timeout(self._timeout_handle)
                    self._timeout_handle = None
                self._iostream.set_close_callback(None)
                del self._events[handle]

        except:
            self.disconnect()
            raise

    def can_read(self, timeout=0):
        "Check if there's any data that can be read"
        if not self._iostream:
            self.connect()

        current = self._get_current_greenlet()
        parent = current.parent

        def check_for_data():
            if (self._parser.can_read() or
                    self._iostream._read_buffer_size):
                return True
            return bool(select([self._iostream.sock], [], [], 0)[0])

        if timeout is 0:
            return check_for_data()
        else:
            self._ioloop.call_later(timeout, current.switch)
            parent.switch()
            return check_for_data()


class AsyncSSLConnection(AsyncConnection):
    description_format = ("AsyncSSLConnection"
                          "<host=%(host)s,port=%(port)s,db=%(db)s>")

    def __init__(self, ssl_keyfile=None, ssl_certfile=None, ssl_cert_reqs=None,
                 ssl_ca_certs=None, **kwargs):
        if ssl_cert_reqs is None:
            ssl_cert_reqs = ssl.CERT_NONE
        elif isinstance(ssl_cert_reqs, basestring):
            CERT_REQS = {
                'none': ssl.CERT_NONE,
                'optional': ssl.CERT_OPTIONAL,
                'required': ssl.CERT_REQUIRED
            }
            if ssl_cert_reqs not in CERT_REQS:
                raise RedisError(
                    "Invalid SSL Certificate Requirements Flag: %s" %
                    ssl_cert_reqs)
            ssl_cert_reqs = CERT_REQS[ssl_cert_reqs]

        self.ssl_options = {
            'keyfile': ssl_keyfile,
            'certfile': ssl_certfile,
            'ca_certs': ssl_ca_certs,
            'cert_reqs': ssl_cert_reqs,
        }

        super(AsyncSSLConnection, self).__init__(**kwargs)

    def _wrap_socket(self, sock):
        return SSLIOStream(sock, ssl_options=self.ssl_options)
