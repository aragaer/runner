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
        self._lf = 0

    def _read(self):
        new_bytes = self._inner.read()
        self._lf = new_bytes.find(b'\n')+1
        if self._lf:
            self._lf += len(self._buffer)
        self._buffer += new_bytes

    def _get_first_line(self):
        result, self._buffer = self._buffer[:self._lf], self._buffer[self._lf:]
        self._lf = self._buffer.find(b'\n')+1
        return result

    def read(self):
        if self._lf:
            return self._get_first_line()

        try:
            self._read()
        except EndpointClosedException:
            if not self._buffer:
                raise

        if self._lf:
            return self._get_first_line()

        try:
            self._read()
        except EndpointClosedException:
            result, self._buffer = self._buffer, b''
            return result
        return b''

    def write(self, *data):
        return self._inner.write(*data)

    def close(self):
        return self._inner.close()
