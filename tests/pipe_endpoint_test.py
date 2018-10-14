import fcntl
import os
import unittest

from runner.channel import EndpointClosedException, PipeChannel


class PipeChannelTest(unittest.TestCase):

    def test_read(self):
        that_faucet_fd, this_sink_fd = os.pipe()
        channel = PipeChannel(faucet=that_faucet_fd)

        sink_file = os.fdopen(this_sink_fd, mode='wb')
        sink_file.write(b'hello, world')
        sink_file.flush()

        self.assertEqual(channel.read(), b'hello, world')
        self.assertEqual(channel.read(), None)
        self.assertEqual(channel.read(), None)

    def test_write(self):
        this_faucet_fd, that_sink_fd = os.pipe()
        channel = PipeChannel(sink=that_sink_fd)

        channel.write(b'hello, world\n')

        faucet_file = os.fdopen(this_faucet_fd, mode='rb')
        fl = fcntl.fcntl(this_faucet_fd, fcntl.F_GETFL)
        fcntl.fcntl(this_faucet_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.assertEqual(faucet_file.readline(), b'hello, world\n')
        self.assertEqual(faucet_file.readline(), b'')
        self.assertEqual(faucet_file.readline(), b'')

    def test_read_write(self):
        that_faucet_fd, this_sink_fd = os.pipe()
        this_faucet_fd, that_sink_fd = os.pipe()
        channel = PipeChannel(faucet=that_faucet_fd, sink=that_sink_fd)

        sink_file = os.fdopen(this_sink_fd, mode='wb')
        sink_file.write(b'hello, world')
        sink_file.flush()
        faucet_file = os.fdopen(this_faucet_fd, mode='rb')
        fl = fcntl.fcntl(this_faucet_fd, fcntl.F_GETFL)
        fcntl.fcntl(this_faucet_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        channel.write(b'hello, world\n')

        self.assertEqual(channel.read(), b'hello, world')
        self.assertEqual(channel.read(), None)
        self.assertEqual(channel.read(), None)
        self.assertEqual(faucet_file.readline(), b'hello, world\n')
        self.assertEqual(faucet_file.readline(), b'')
        self.assertEqual(faucet_file.readline(), b'')

    def test_write_list(self):
        this_faucet_fd, that_sink_fd = os.pipe()
        channel = PipeChannel(sink=that_sink_fd)

        channel.write(b'hello, ', b'world\n')

        faucet_file = os.fdopen(this_faucet_fd, mode='rb')
        fl = fcntl.fcntl(this_faucet_fd, fcntl.F_GETFL)
        fcntl.fcntl(this_faucet_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.assertEqual(faucet_file.readline(), b'hello, world\n')
        self.assertEqual(faucet_file.readline(), b'')
        self.assertEqual(faucet_file.readline(), b'')

    def test_closed_read(self):
        that_faucet_fd, _ = os.pipe()
        faucet = PipeChannel(that_faucet_fd)

        os.close(that_faucet_fd)

        with self.assertRaises(EndpointClosedException):
            faucet.read()

    def test_close_read(self):
        that_faucet_fd, _ = os.pipe()
        channel = PipeChannel(faucet=that_faucet_fd)
        channel.close()

        with self.assertRaises(OSError) as ose:
            os.read(that_faucet_fd, 1)
            self.assertEqual(ose.exception.error_code, 9)  # EBADF

    def test_closed_write(self):
        _, that_sink_fd = os.pipe()
        channel = PipeChannel(sink=that_sink_fd)

        os.close(that_sink_fd)

        with self.assertRaises(EndpointClosedException):
            channel.write(b' ')

    def test_close(self):
        _, that_sink_fd = os.pipe()
        sink = PipeChannel(sink=that_sink_fd)

        sink.close()

        with self.assertRaises(OSError) as ose:
            os.write(that_sink_fd, b' ')
            self.assertEqual(ose.exception.error_code, 9)  # EBADF

    def test_write_close_read(self):
        that_faucet_fd, this_sink_fd = os.pipe()
        channel = PipeChannel(faucet=that_faucet_fd)

        sink_file = os.fdopen(this_sink_fd, mode='wb')
        sink_file.write(b'hello, world')
        sink_file.close()

        self.assertEqual(channel.read(), b'hello, world')
        self.assertEqual(channel.read(), b'')

    def test_get_fd_read(self):
        that_faucet_fd, this_sink_fd = os.pipe()
        channel = PipeChannel(faucet=that_faucet_fd)

        self.assertEqual(channel.get_fd(), that_faucet_fd)

    def test_get_fd_write_only(self):
        that_faucet_fd, this_sink_fd = os.pipe()
        channel = PipeChannel(sink=this_sink_fd)

        with self.assertRaises(NotImplementedError):
            channel.get_fd()
