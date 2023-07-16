import os
import shutil
import signal
import stat
import time
import unittest

from pathlib import Path
from tempfile import mkdtemp, mkstemp

from channels import EndpointClosedException, Channel

from runner import Runner, ProcessExistsException


def readline(channel):
    for _ in range(1000):
        time.sleep(0.001)
        line = channel.read()
        if line is not None:
            return line


class RunnerTest(unittest.TestCase):

    _runner = None

    def setUp(self):
        self._runner = Runner()

    def test_cat(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat')

        channel = self._runner.get_channel('cat')

        self.assertTrue(isinstance(channel, Channel))
        channel.write(b'hello, world')

        self.assertEquals(readline(channel), b'hello, world')

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
        self.assertEquals(readline(channel), b'hello, world')

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
        self.assertEquals(readline(channel), b'{"message": "test"}\n')

    def test_alias(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat', alias='cat0')

        channel = self._runner.get_channel('cat0')

        channel.write(b'hello, world')
        self.assertEquals(readline(channel), b'hello, world')

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
        self.assertEquals(readline(channel1), b'{"message": "test1"}\n')
        channel2 = self._runner.get_channel('cat2')
        self.assertEquals(readline(channel2), b'{"message": "test2"}\n')

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
        self.assertEquals(readline(channel), b'hello, world')

    def test_wait_socket(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        sockname = os.path.join(dirname, "socket")

        cmd = 'sh -c "sleep 0.01; socat SYSTEM:cat UNIX-LISTEN:{}"'.format(sockname)
        self._runner.update_config({"socat":
                                    {"command": cmd,
                                     "type": "socket",
                                     "cwd": dirname}})

        self._runner.ensure_running('socat', socket=sockname)

        channel = self._runner.get_channel('socat')
        channel.write(b'hello, world')
        self.assertEquals(readline(channel), b'hello, world')

    def test_terminate_restart(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
        self._runner.ensure_running('cat')

        self._runner.terminate('cat')

        self._runner.ensure_running('cat')

        chan = self._runner.get_channel('cat')
        chan.write(b'hello')
        self.assertEqual(readline(chan), b'hello')

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
        self.assertEqual(readline(chan), b'hello, world\n')

    def test_setpgrp_false(self):
        self._runner.update_config({"sleep_echo": {"command": 'sh -c "read a; echo test"'}})

        self._runner.start("sleep_echo")
        with self.assertRaises(KeyboardInterrupt):
            os.killpg(os.getpgrp(), signal.SIGINT)

        time.sleep(0.01)

        with self.assertRaises(EndpointClosedException):
            self._runner.get_channel('sleep_echo').write(b'\n')

    def test_setpgrp_true(self):
        self._runner.update_config({"sleep_echo": {"command": 'sh -c "read a; echo test"',
                                                   "setpgrp": True}})

        self._runner.start("sleep_echo")
        with self.assertRaises(KeyboardInterrupt):
            os.killpg(os.getpgrp(), signal.SIGINT)

        if os.environ.get('TRAVIS', False):
            raise unittest.SkipTest("setpgrp doesn't work on travis")

        chan = self._runner.get_channel('sleep_echo')
        chan.write(b'\n')
        self.assertEqual(readline(chan), b'test\n', "Child process is not killed")

    def test_register_cat(self):
        self._runner.add("cat", command="cat")
        self._runner.start('cat')

        channel = self._runner.get_channel('cat')
        channel.write(b'hello, world')

        self.assertEquals(readline(channel), b'hello, world')

    def test_extra_kwargs_override_kwargs(self):
        self._runner.update_config({"cat": {"command": "cat", "type": "stdio", "buffering": "line"}})
        self._runner.ensure_running('cat', buffering=None)

        channel = self._runner.get_channel('cat')

        self.assertTrue(isinstance(channel, Channel))
        channel.write(b'hello, world')

        self.assertEquals(readline(channel), b'hello, world')

    def test_extra_kwargs_override_cwd(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        with open(os.path.join(dirname, "file"), "w") as file:
            file.write('{"message": "test"}\n')

        self._runner.update_config({"cat":
                                    {"command": "cat file",
                                     "type": "stdio",
                                     "cwd": 'xxx'}})

        self._runner.ensure_running('cat', cwd=dirname)

        channel = self._runner.get_channel('cat')
        self.assertTrue(isinstance(channel, Channel))
        self.assertEquals(readline(channel), b'{"message": "test"}\n')


class RunnerConstructorTest(unittest.TestCase):

    def test_path(self):
        dirname = mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(dirname))
        scrfd, scrpath = mkstemp(dir=dirname)
        with os.fdopen(scrfd, "w") as scr:
            scr.write("#!/bin/sh\necho hello, world\n")
        script = Path(scrpath)
        script.chmod(stat.S_IRUSR | stat.S_IXUSR)

        other_script = Path(dirname) / "script"
        other_script.write_text(f"#!/bin/sh\n{script.name}\n")
        other_script.chmod(stat.S_IRUSR | stat.S_IXUSR)

        runner = Runner(extra_paths=[dirname])

        runner.add("script", str(other_script), buffering='line')
        runner.ensure_running('script')

        channel = runner.get_channel('script')
        line = readline(channel)
        print(line.decode())
        self.assertEquals(line, b'hello, world\n')
