import socket
import unittest

from runner.channel import Channel, EndpointClosedException
from runner.poller import Poller
from runner.testing import TestChannel

from utils import timeout


class PollerTest(unittest.TestCase):

    def setUp(self):
        self._poller = Poller()

    def tearDown(self):
        self._poller.close_all()

    def test_blocking_poll(self):
        with self.assertRaisesRegex(Exception, "timeout"), timeout(0.02):
            self._poller.poll()

    def test_timed_poll(self):
        with timeout(0.02):
            result = self._poller.poll(0.01)
        self.assertEqual(list(result), [])

    def test_timed_out_poll(self):
        with self.assertRaisesRegex(Exception, "timeout"), timeout(0.02):
            self._poller.poll(0.03)

    def test_poll_data(self):
        chan = TestChannel()
        self._poller.register(chan)
        chan.put(b'hello\n')

        with timeout(0.02):
            result = self._poller.poll()

        self.assertEqual(list(result), [(b'hello\n', chan)])

    def test_poll_no_data(self):
        chan = TestChannel()
        self._poller.register(chan)

        with timeout(0.02):
            result = self._poller.poll(0.01)

        self.assertEqual(list(result), [])

    def _setup_server(self):
        serv = socket.socket()
        serv.bind(('127.0.0.1', 0))
        serv.listen(0)
        self.addCleanup(serv.close)
        return serv

    def test_poll_accept(self):
        serv = self._setup_server()
        addr, port = serv.getsockname()

        self._poller.add_server(serv)

        client = socket.create_connection((addr, port))
        cl_addr = client.getsockname()
        result = list(self._poller.poll(0.01))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0][0], cl_addr)
        self.assertIsInstance(result[0][0][1], Channel)
        self.assertEqual(result[0][1], serv)

        cl_chan = result[0][0][1]

        client.send(b'hello\n')

        result = self._poller.poll(0.01)
        self.assertEqual(list(result), [(b'hello\n', cl_chan)])

    def test_close_all_channels(self):
        chan = TestChannel()
        self._poller.register(chan)

        self._poller.close_all()

        with self.assertRaises(ValueError):
            chan.read()

    def test_close_all_servers(self):
        serv = self._setup_server()
        self._poller.add_server(serv)

        self._poller.close_all()

        with timeout(0.01), self.assertRaises(OSError):
            serv.accept()

    def test_unregister(self):
        chan = TestChannel()
        self._poller.register(chan)
        chan.put(b'hello\n')

        self._poller.unregister(chan)

        with self.assertRaisesRegex(Exception, "timeout"), timeout(0.02):
            self._poller.poll()

    def test_closed(self):
        chan = TestChannel()
        self._poller.register(chan)

        chan.close()

        with timeout(0.01):
            result = self._poller.poll()

        self.assertEquals(result, [(b'', chan)])

    def test_disconnect(self):
        serv = self._setup_server()
        addr, port = serv.getsockname()
        self._poller.add_server(serv)
        client = socket.create_connection((addr, port))
        result = list(self._poller.poll(0.01))  # accepts the client
        cl_chan = result[0][0][1]

        client.close()
        result = list(self._poller.poll(0.01))

        self.assertEqual(result, [(b'', cl_chan)])
