import os
import unittest

from runner.testing import TestChannel


class TestChannelTest(unittest.TestCase):

    def setUp(self):
        self._chan = TestChannel()

    def tearDown(self):
        self._chan.close()

    def test_read_empty(self):
        self.assertEqual(self._chan.read(), b'')

    def test_read(self):
        self._chan.put(b'Hello')

        self.assertEqual(self._chan.read(), b'Hello')

    def test_get(self):
        self.assertEqual(self._chan.get(), b'')

    def test_write(self):
        self._chan.write(b'hi')
        
        self.assertEqual(self._chan.get(), b'hi')

    def test_get_fd(self):
        fd = self._chan.get_fd()

        self._chan.put(b'test')

        self.assertEqual(os.fdopen(os.dup(fd)).read(), 'test')
