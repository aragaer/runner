import socket
import unittest

from runner.channel import EndpointClosedException, SocketChannel


class SocketChannelTest(unittest.TestCase):

    _server = None
    _client = None
    _channel = None

    def setUp(self):
        self._server, self._client = socket.socketpair()
        self.addCleanup(self._server.close)
        self.addCleanup(self._client.close)
        self._channel = SocketChannel(self._client)

    def test_read(self):
        self._server.send(b'hello, world')

        self.assertEqual(self._channel.read(), b'hello, world')
        self.assertEqual(self._channel.read(), None)
        self.assertEqual(self._channel.read(), None)

    def test_write(self):
        self._channel.write(b'hello, world')

        self.assertEqual(self._server.recv(4096), b'hello, world')

    def test_write_list(self):
        self._channel.write(b'hello, ', b'world')

        self.assertEqual(self._server.recv(4096), b'hello, world')

    def test_closed_read(self):
        self._client.close()

        with self.assertRaises(EndpointClosedException):
            self._channel.read()

    def test_close_read(self):
        self._channel.close()

        with self.assertRaises(OSError) as ose:
            self._client.recv(1)
            self.assertEqual(ose.exception.error_code, 9)  # EBADF

    def test_closed_write(self):
        self._client.close()

        with self.assertRaises(EndpointClosedException):
            self._channel.write(b' ')

    def test_close_write(self):
        self._channel.close()

        with self.assertRaises(OSError) as ose:
            self._client.send(b' ')
            self.assertEqual(ose.exception.error_code, 9)  # EBADF

    def test_write_close_read(self):
        self._server.send(b'hello, world')
        self._server.close()

        self.assertEqual(self._channel.read(), b'hello, world')
        self.assertEqual(self._channel.read(), b'')

    def test_get_fd(self):
        self.assertEqual(self._channel.get_fd(), self._client.fileno())
