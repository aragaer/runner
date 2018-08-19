import logging
import os
import shlex
import socket
import subprocess
import time

import runner.channel as channel

_LOGGER = logging.getLogger(__name__)


class ProcessExistsException(Exception):
    pass


class Proc:

    def __init__(self, proc, chan):
        self._proc = proc
        self._channel = chan

    @property
    def channel(self):
        return self._channel

    def terminate(self):
        self._channel.close()
        self._proc.terminate()
        self._proc.wait()


class App:

    def __init__(self, command, type="stdio", **kwargs):
        self._command = shlex.split(command)
        self._type = type
        self._kwargs = kwargs

    @staticmethod
    def _connect_socket(sockname):
        sock = socket.socket(socket.AF_UNIX)
        _LOGGER.debug("Waiting for socket %s", sockname)
        while not os.path.exists(sockname):
            time.sleep(0.1)
        sock.connect(sockname)
        return channel.SocketChannel(sock)

    def start(self, extra_args, **extra_kwargs):
        kwargs = {**extra_kwargs, **self._kwargs}
        if self._type == 'stdio':
            stdin = stdout = subprocess.PIPE
        elif self._type == 'socket':
            sockname = kwargs['socket']
            stdin = stdout = None
            if os.path.exists(sockname):
                os.unlink(sockname)
        command = self._command[:]
        if extra_args is not None:
            command += extra_args
        preexec_fn = None
        if kwargs.get('setpgrp', False):
            preexec_fn = os.setpgrp
        proc = subprocess.Popen(command,
                                stdin=stdin,
                                stdout=stdout,
                                preexec_fn=preexec_fn,
                                cwd=self._kwargs.get('cwd'))
        if self._type == 'stdio':
            chan = channel.PipeChannel(sink=proc.stdin.fileno(),
                                       faucet=proc.stdout.fileno())
        elif self._type == 'socket':
            chan = self._connect_socket(sockname)
        if kwargs.get("buffering") == "line":
            chan = channel.LineChannel(chan)
        return Proc(proc, chan)


class Runner:

    def __init__(self):
        self._apps = {}
        self._procs = {}

    def update_config(self, config):
        for app, app_config in config.items():
            _LOGGER.debug("Updating config for %s", app)
            self._apps[app] = App(**app_config)

    def ensure_running(self, app_name, alias=None, with_args=None, **kwargs):
        if alias is None:
            alias = app_name
        if alias in self._procs:
            _LOGGER.info("Application alias %s is already taken, not starting %s", alias, app_name)
            return
        _LOGGER.info("Starting application %s as %s", app_name, alias)
        self._procs[alias] = self._apps[app_name].start(with_args, **kwargs)
        _LOGGER.debug("%s started", alias)

    def start(self, app_name, alias=None, with_args=None, **kwargs):
        if alias is None:
            alias = app_name
        if alias in self._procs:
            raise ProcessExistsException
        self.ensure_running(app_name, alias, with_args, **kwargs)

    def get_channel(self, alias):
        if alias in self._procs:
            return self._procs[alias].channel

    def terminate(self, alias):
        proc = self._procs[alias]
        proc.terminate()
        del self._procs[alias]
