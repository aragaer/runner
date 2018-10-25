import logging

from .proc import App

_LOGGER = logging.getLogger(__name__)


class ProcessExistsException(Exception):
    pass


class Runner:

    def __init__(self):
        self._apps = {}
        self._procs = {}

    def add(self, app, command, **kwargs):
        self.update_config({app: dict(command=command, **kwargs)})

    def update_config(self, config):
        for app, app_config in config.items():
            _LOGGER.debug("Updating config for %s", app)
            self._apps[app] = App(**app_config)

    def ensure_running(self, app_name, alias=None, with_args=None, **kwargs):
        if alias is None:
            alias = app_name
        if alias in self._procs:
            _LOGGER.info("Application alias %s is already taken, not starting %s",
                         alias, app_name)
            return
        if with_args is None:
            with_args = []
        _LOGGER.info("Starting application %s as %s", app_name, alias)
        self._procs[alias] = self._apps[app_name].start(*with_args, **kwargs)
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
