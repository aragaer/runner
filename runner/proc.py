import logging
import os
import shlex
import socket
import subprocess
import time

from abc import ABCMeta, abstractmethod

import attr
import channels


_LOGGER = logging.getLogger(__name__)


@attr.s(frozen=True)
class _Proc:
    proc = attr.ib()
    channel = attr.ib()

    def terminate(self):
        self.channel.close()
        self.proc.terminate()
        self.proc.wait()


@attr.s
class _ProcStarter(metaclass=ABCMeta):
    command = attr.ib()
    buffering = attr.ib()
    cwd = attr.ib()
    preexec_fn = attr.ib(init=False, default=None)
    proc = attr.ib(init=False)
    stdin = attr.ib(init=False)
    stdout = attr.ib(init=False)

    @abstractmethod
    def pre_start(self): #pragma: no cover
        pass

    @abstractmethod
    def get_channel(self): #pragma: no cover
        pass

    def start(self):
        self.pre_start()
        self.proc = subprocess.Popen(self.command,
                                     stdin=self.stdin,
                                     stdout=self.stdout,
                                     preexec_fn=self.preexec_fn,
                                     cwd=self.cwd)

        return _Proc(self.proc, self.get_channel())


@attr.s
class _PipeProcStarter(_ProcStarter):

    def __attrs_post_init__(self):
        self.stdin = self.stdout = subprocess.PIPE

    def get_channel(self):
        return channels.PipeChannel(sink=self.proc.stdin.fileno(),
                                    faucet=self.proc.stdout.fileno(),
                                    buffering=self.buffering)

    def pre_start(self):
        pass


@attr.s
class _SocketProcStarter(_ProcStarter):
    sockname = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.stdin = self.stdout = None

    def get_channel(self):
        sock = socket.socket(socket.AF_UNIX)
        _LOGGER.debug("Waiting for socket %s", self.sockname)
        while not os.path.exists(self.sockname):
            time.sleep(0.01)
        sock.connect(self.sockname)
        return channels.SocketChannel(sock,
                                      buffering=self.buffering)

    def pre_start(self):
        if os.path.exists(self.sockname):
            os.unlink(self.sockname)


class App:

    def __init__(self, command, type="stdio", **kwargs):
        self._command = shlex.split(command)
        self._kwargs = kwargs
        if type == 'stdio':
            self._ps_class = _PipeProcStarter
        else:
            self._ps_class = _SocketProcStarter

    def start(self, *extra_args, **extra_kwargs):
        kwargs = dict(self._kwargs, **extra_kwargs)
        ps = self._ps_class(self._command + list(extra_args),
                            cwd=kwargs.get('cwd'),
                            buffering=kwargs.get('buffering'))
        if kwargs.get('setpgrp', False):
            ps.preexec_fn = os.setpgrp
        if self._ps_class == _SocketProcStarter:
            ps.sockname = kwargs['socket']
        return ps.start()
