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

    def get_fd(self): #pragma: no cover
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
            return self._in.read()
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

    def get_fd(self):
        if self._in is not None:
            return self._in.fileno()
        return super().get_fd()


class SocketChannel(Channel):

    def __init__(self, sock):
        self._sock = sock
        self._sock.setblocking(False)

    def read(self):
        try:
            return self._sock.recv(4096)
        except BlockingIOError:
            return None
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

    def get_fd(self):
        return self._sock.fileno()


class LineChannel(Channel):

    def __init__(self, inner):
        self._inner = inner
        self._buffer = b''
        self._lf = 0

    def _get_first_line(self):
        result, self._buffer = self._buffer[:self._lf], self._buffer[self._lf:]
        self._lf = self._buffer.find(b'\n')+1
        return result

    def read(self):
        for _ in range(2):
            if self._lf:
                return self._get_first_line()

            new_bytes = self._inner.read()
            if new_bytes is None:
                return

            if not new_bytes:
                result, self._buffer = self._buffer, b''
                return result

            lf = new_bytes.find(b'\n')+1
            if lf:
                self._lf = lf + len(self._buffer)
            self._buffer += new_bytes

    def write(self, *data):
        return self._inner.write(*data)

    def close(self):
        return self._inner.close()

    def get_fd(self):
        return self._inner.get_fd()
