import time
import unittest

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
        self._runner.add("cat", "cat", buffering="line")
        self._runner.start('cat')
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
        self._runner.add("echo", "echo -n")
    
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
