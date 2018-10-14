# Runner [![Build Status](https://travis-ci.org/aragaer/runner.svg?branch=master)](https://travis-ci.org/aragaer/runner) [![codecov](https://codecov.io/gh/aragaer/runner/branch/master/graph/badge.svg)](https://codecov.io/gh/aragaer/runner) [![BCH compliance](https://bettercodehub.com/edge/badge/aragaer/runner?branch=master)](https://bettercodehub.com/) [![donate using paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=aragaer@gmail.com&lc=RU&item_name=RUNNER&currency_code=USD&bn=PP-DonationsBF:btn_donate_SM.gif:NonHosted)

Simple wrapper around subprocess.Popen.

Multiple commands can be configured to be executed. Each command can
have some predetermined parameters and additional parameters or
overrides can be passed when application is executed. Multiple
instances of one application can be running using aliases.

To communicate to running processes Channel classes from
[yet-another-io-channels-library](https://github.com/aragaer/channels)
are used.

Examples:

Using STDIO.

    runner = Runner()
    runner.add("cat", "cat")
    runner.start('cat')
    channel = runner.get_channel('cat')
    channel.write(b'hello, world')
	# later
	line = channel.read() # Will return b'hello, world'

Using UNIX socket.

    runner = Runner()
    self._runner.add("socat", "socat SYSTEM:cat UNIX-LISTEN:socket",
	                 type="socket", socket="socket")
    runner.start('socat')
    channel = runner.get_channel('socat')
    channel.write(b'hello, world')
	# later
	line = channel.read() # Will return b'hello, world'

## Classes

### Runner

`add(self, name, command, **kwargs)`

Add the application to the list of registered applications or update
if already added.

- `name`: application name
- `command`: the command to be executed

`**kwargs` can include the following:

- `type`: either `stdio` or `socket`. Default is `stdio`
- `cwd`: working directory of the process
- `socket`: if type is `socket`, this is the name of the UNIX socket file to connect to
- `setpgrp`: if `True` the process is moved to a separate process group and will not receive signals sent to main process. Default is `False`
- `buffering`: if set to `"line"` the channel is line-buffered for reading

`update_config(self, config)`

Config must be a dictionary where each key is an alias of an
application and value is a dictionary of that application's
configuration. `runner.add("app", "command", **kwargs)` is equivalent
to `runner.update_config({"app": {"command": "command",
**kwargs}})`. Useful for adding multiple applications at once.

`ensure_running(self, app_name, alias=None, with_args=None, **kwargs)`

`start(self, app_name, alias=None, with_args=None, **kwargs)`

Start the process. If the process with the same alias is already
running, `start` will raise `ProcessExistsException`, while
`ensure_running` will silently do nothing.

- `app_name`: application alias, given in the configuration
- `alias`: alias that will be given to actual started process. If `None`, application alias will be used
- `with_args`: list of additional arguments that will be added to the command
- `kwargs`: extend or override parameters in application config

`get_channel(self, alias)`

Returns the `Channel` object to communicate to the running process.

`terminate(self, alias)`

Terminates the process.
