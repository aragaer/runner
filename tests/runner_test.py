import os
import shutil
import time
import unittest

from tempfile import mkdtemp

from runner.channel import EndpointClosedException, Channel
from runner import Runner, ProcessExistsException


class RunnerTest(unittest.TestCase):

    _runner = None

    def setUp(self):
        self._runner = Runner()

    @staticmethod
    def _readline(channel):
        for _ in range(100):
            time.sleep(0.001)
            line = channel.read()
            if line is not None:
                return line

    def test_cat(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat')

        channel = self._runner.get_channel('cat')

        self.assertTrue(isinstance(channel, Channel))
        channel.write(b'hello, world')

        self.assertEquals(self._readline(channel), b'hello, world')

    def test_cat_socat(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        sockname = os.path.join(dirname, "socket")

        self._runner.update_config({"socat":
                                    {"command": "socat SYSTEM:cat UNIX-LISTEN:"+sockname,
                                     "type": "socket",
                                     "socket": sockname}})

        self._runner.ensure_running('socat')

        channel = self._runner.get_channel('socat')
        channel.write(b'hello, world')
        self.assertEquals(self._readline(channel), b'hello, world')

    def test_cwd(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        with open(os.path.join(dirname, "file"), "w") as file:
            file.write('{"message": "test"}\n')

        self._runner.update_config({"cat":
                                    {"command": "cat file",
                                     "type": "stdio",
                                     "cwd": dirname}})

        self._runner.ensure_running('cat')

        channel = self._runner.get_channel('cat')
        self.assertTrue(isinstance(channel, Channel))
        self.assertEquals(self._readline(channel), b'{"message": "test"}\n')

    def test_alias(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat', alias='cat0')

        channel = self._runner.get_channel('cat0')

        channel.write(b'hello, world')
        self.assertEquals(self._readline(channel), b'hello, world')

    def test_extra_args(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        with open(os.path.join(dirname, "file1"), "w") as file:
            file.write('{"message": "test1"}\n')
        with open(os.path.join(dirname, "file2"), "w") as file:
            file.write('{"message": "test2"}\n')

        self._runner.update_config({"cat":
                                    {"command": "cat",
                                     "type": "stdio",
                                     "cwd": dirname}})

        self._runner.ensure_running('cat', alias="cat1", with_args=['file1'])
        self._runner.ensure_running('cat', alias="cat2", with_args=['file2'])

        channel1 = self._runner.get_channel('cat1')
        self.assertEquals(self._readline(channel1), b'{"message": "test1"}\n')
        channel2 = self._runner.get_channel('cat2')
        self.assertEquals(self._readline(channel2), b'{"message": "test2"}\n')

    def test_terminate(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat')
        chan = self._runner.get_channel('cat')

        self._runner.terminate('cat')

        self.assertIsNone(self._runner.get_channel('cat'))

        with self.assertRaises(EndpointClosedException):
            chan.read()

        with self.assertRaises(EndpointClosedException):
            chan.write(b' ')

    def test_terminate_socket(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        sockname = os.path.join(dirname, "socket")

        self._runner.update_config({"socat":
                                    {"command": "socat SYSTEM:cat UNIX-LISTEN:"+sockname,
                                     "type": "socket",
                                     "socket": sockname}})

        self._runner.ensure_running('socat')
        chan = self._runner.get_channel('socat')

        self._runner.terminate('socat')

        self.assertIsNone(self._runner.get_channel('socat'))

        with self.assertRaises(EndpointClosedException):
            chan.read()

        with self.assertRaises(EndpointClosedException):
            chan.write(b' ')

    def test_socket_arg(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        sockname = os.path.join(dirname, "socket")
        with open(sockname, "w") as file:
            file.write("")

        self._runner.update_config({"socat":
                                    {"command": "socat SYSTEM:cat UNIX-LISTEN:"+sockname,
                                     "type": "socket",
                                     "cwd": dirname}})

        self._runner.ensure_running('socat', socket=sockname)

        channel = self._runner.get_channel('socat')
        channel.write(b'hello, world')
        self.assertEquals(self._readline(channel), b'hello, world')

    def test_wait_socket(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        sockname = os.path.join(dirname, "socket")

        cmd = 'sh -c "sleep 0.1; socat SYSTEM:cat UNIX-LISTEN:{}"'.format(sockname)
        self._runner.update_config({"socat":
                                    {"command": cmd,
                                     "type": "socket",
                                     "cwd": dirname}})

        self._runner.ensure_running('socat', socket=sockname)

        channel = self._runner.get_channel('socat')
        channel.write(b'hello, world')
        self.assertEquals(self._readline(channel), b'hello, world')

    def test_terminate_restart(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat')

        self._runner.terminate('cat')

        self._runner.ensure_running('cat')

        chan = self._runner.get_channel('cat')
        chan.write(b'hello')
        self.assertEqual(self._readline(chan), b'hello')

    def test_start(self):
        self._runner.update_config({"sleep": {"command": "sleep 5", "type": "stdio"}})
        self.addCleanup(lambda: self._runner.terminate('sleep'))

        self._runner.start('sleep')

        with self.assertRaises(ProcessExistsException):
            self._runner.start('sleep')

    def test_ensure_running_twice(self):
        self._runner.update_config({"echo": {"command": "echo", "type": "stdio"}})

        self._runner.ensure_running("echo", with_args=["hello, world"])
        self._runner.ensure_running("echo", with_args=["goodbye, world"])

        chan = self._runner.get_channel('echo')
        self.assertEqual(self._readline(chan), b'hello, world\n')
