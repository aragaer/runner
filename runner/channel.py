import fcntl
import io
import os
import socket

from abc import ABCMeta, abstractmethod


class EndpointClosedException(Exception):
    pass


class Channel(metaclass=ABCMeta):

    @abstractmethod
    def read(self): #pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def write(self, data): #pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def close(self): #pragma: no cover
        raise NotImplementedError

    def get_fd(self): #pragma: no cover
        raise NotImplementedError


class PipeChannel(Channel):

    def __init__(self, faucet=None, sink=None):
        f_in, f_out = None, None
        self._fileno = None
        if faucet is not None:
            fl = fcntl.fcntl(faucet, fcntl.F_GETFL)
            fcntl.fcntl(faucet, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            f_in = os.fdopen(faucet, mode='rb')
            self._fileno = faucet
        if sink is not None:
            f_out = os.fdopen(sink, mode='wb', buffering=0)

        if f_in and f_out:
            self._io = io.BufferedRWPair(f_in, f_out, 1)
        elif f_in:
            self._io = f_in
        else:
            self._io = f_out

    def read(self):
        return self._io.read()

    def write(self, data):
        self._io.write(data)

    def close(self):
        self._io.close()

    def get_fd(self):
        if self._fileno is None:
            return super().get_fd()
        return self._fileno


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

    def write(self, data):
        try:
            self._sock.send(data)
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

    def write(self, data):
        return self._inner.write(data)

    def close(self):
        return self._inner.close()

    def get_fd(self):
        return self._inner.get_fd()
