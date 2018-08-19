import time
import unittest

from runner.channel import Channel, EndpointClosedException, LineChannel
from runner import Runner


def _readall(channel):
    for _ in range(100):
        time.sleep(0.001)
        line = channel.read()
        if line is not None:
            return line

class RunnerBufferingTest(unittest.TestCase):

    _runner = None

    def setUp(self):
        self._runner = Runner()
        self._runner.update_config({"cat": {"command": "cat", "buffering": "line"}})
        self._runner.ensure_running('cat')
        self.addCleanup(lambda: self._runner.terminate("cat"))
        self._chan = self._runner.get_channel('cat')

    def test_read_one_line(self):
        self._chan.write(b'test\n')

        self.assertEqual(_readall(self._chan), b'test\n')

    def test_read_partial(self):
        self._chan.write(b'te')

        self.assertEqual(_readall(self._chan), b'')

        self._chan.write(b'st\nx')

        self.assertEqual(_readall(self._chan), b'test\n')


class ReadAfterDoneTest(unittest.TestCase):
    _runner = None

    def setUp(self):
        self._runner = Runner()
        self._runner.update_config({"echo": {"command": "echo -n"}})
    
    def test_read_after_done(self):
        self._runner.start("echo", with_args=["test"])
        self.addCleanup(lambda: self._runner.terminate("echo"))
        chan = self._runner.get_channel("echo")

        self.assertEqual(_readall(chan), b'test')

    def test_buffered_read_after_done(self):
        self._runner.start("echo", with_args=["test"], buffering='line')
        self.addCleanup(lambda: self._runner.terminate("echo"))
        chan = self._runner.get_channel("echo")

        self.assertEqual(_readall(chan), b'test')


class SimpleChannel(Channel):

    _bytes = b''
    _closed = False

    def read(self):
        if self._closed and not self._bytes:
            raise EndpointClosedException
        result, self._bytes = self._bytes, b''
        return result

    def write(self, *data):
        if self._closed:
            raise EndpointClosedException
        self._bytes += b''.join(data)

    def close(self):
        self._closed = True


class LineBufferingTest(unittest.TestCase):

    def setUp(self):
        self._inner = SimpleChannel()
        self._chan = LineChannel(self._inner)

    def test_write_line(self):
        self._chan.write(b'test\n')

        self.assertEqual(self._chan.read(), b'test\n')

    def test_write_partial(self):
        self._chan.write(b'te')

        self.assertEqual(self._chan.read(), b'')

    def test_write_two_step(self):
        self._chan.write(b'te')

        self.assertEqual(self._chan.read(), b'')

        self._chan.write(b'st\n')

        self.assertEqual(self._chan.read(), b'test\n')
        self.assertEqual(self._chan.read(), b'')

    def test_write_more_than_one_line(self):
        self._chan.write(b'a\nb\n')

        self.assertEqual(self._chan.read(), b'a\n')
        self.assertEqual(self._chan.read(), b'b\n')

    def test_read_last_line(self):
        self._chan.write(b'test')

        self._inner.close()

        self.assertEqual(self._chan.read(), b'test')

    def test_read_including_last_line(self):
        self._chan.write(b'hello\nworld')

        self._inner.close()

        self.assertEqual(self._chan.read(), b'hello\n')
        self.assertEqual(self._chan.read(), b'world')
        with self.assertRaises(EndpointClosedException):
            print(self._chan.read())
