import fcntl
import os

from abc import ABCMeta, abstractmethod


class EndpointClosedException(Exception):
    pass


class Channel(metaclass=ABCMeta):

    @abstractmethod
    def read(self): #pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def write(self, *data): #pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def close(self): #pragma: no cover
        raise NotImplementedError


class PipeChannel(Channel):

    _in = None
    _out = None

    def __init__(self, faucet=None, sink=None):
        if faucet is not None:
            fl = fcntl.fcntl(faucet, fcntl.F_GETFL)
            fcntl.fcntl(faucet, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            self._in = os.fdopen(faucet, mode='rb')
        if sink is not None:
            self._out = os.fdopen(sink, mode='wb')

    def read(self):
        try:
            result = self._in.read()
            if result is None:
                return b''
            if not result:
                raise EndpointClosedException()
            return result
        except (ValueError, OSError) as ex:
            raise EndpointClosedException(ex)

    def write(self, *data):
        try:
            for d in data:
                self._out.write(d)
            self._out.flush()
        except (ValueError, OSError) as ex:
            raise EndpointClosedException(ex)

    def close(self):
        if self._in is not None:
            self._in.close()
        if self._out is not None:
            self._out.close()


class SocketChannel(Channel):

    def __init__(self, sock):
        self._sock = sock
        self._sock.setblocking(False)

    def read(self):
        try:
            result = self._sock.recv(4096)
            if not result:
                raise EndpointClosedException()
            return result
        except BlockingIOError:
            return b''
        except OSError as ex:
            raise EndpointClosedException(ex)

    def write(self, *data):
        try:
            for d in data:
                self._sock.send(d)
        except OSError as ex:
            raise EndpointClosedException(ex)

    def close(self):
        self._sock.close()


class LineChannel(Channel):

    def __init__(self, inner):
        self._inner = inner
        self._buffer = b''

    def read(self):
        if b'\n' not in self._buffer:
            try:
                self._buffer += self._inner.read()
            except EndpointClosedException:
                if not self._buffer:
                    raise
        if b'\n' in self._buffer:
            result, self._buffer = self._buffer.split(b'\n', 1)
            return result+b'\n'
        try:
            self._buffer += self._inner.read()
        except EndpointClosedException:
            result, self._buffer = self._buffer, b''
            return result
        return b''

    def write(self, *data):
        return self._inner.write(*data)

    def close(self):
        return self._inner.close()
