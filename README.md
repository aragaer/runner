# Runner [![Build Status](https://travis-ci.org/aragaer/runner.svg?branch=master)](https://travis-ci.org/aragaer/runner) [![codecov](https://codecov.io/gh/aragaer/runner/branch/master/graph/badge.svg)](https://codecov.io/gh/aragaer/runner)[![BCH compliance](https://bettercodehub.com/edge/badge/aragaer/runner?branch=master)](https://bettercodehub.com/)

Simple wrapper around subprocess.Popen.

Multiple commands can be configured to be executed. Each command can have some predetermined parameters and additional parameters or overrides can be passed when application is executed. Multiple instances of one application can be running using aliases.

To communicate to running processes Channel classes are used. These provide non-blocking byte-oriented data. Currently STDIO and UNIX socket are supported.

Examples:

Using STDIO.

    runner = Runner()
    runner.update_config({"cat": {"command": "cat", "type": "stdio"}})
    runner.ensure_running('cat')
    channel = runner.get_channel('cat')
    channel.write(b'hello, world')
	# later
	line = channel.read() # Will return b'hello, world'

Using UNIX socket.

    runner = Runner()
    self._runner.update_config({"socat":
                                {"command": "socat SYSTEM:cat UNIX-LISTEN:socket",
                                 "type": "socket",
                                 "socket": "socket"}})
    runner.ensure_running('socat')
    channel = runner.get_channel('socat')
    channel.write(b'hello, world')
	# later
	line = channel.read() # Will return b'hello, world'

## Classes

### Runner

`update_config(self, config)`

Config must be a dictionary where each key is an alias of an application and value is a dictionary of that application's configuration. The following fields are expected:

- `command` (required): The command to be executed
- `type`: Either `stdio` or `socket`. Default is `stdio`
- `cwd`: Working directory of the process
- `socket`: if type is `socket`, this is the name of the UNIX socket file to connect to

`ensure_running(self, app_name, alias=None, with_args=None, **kwargs)`

`start(self, app_name, alias=None, with_args=None, **kwargs)`

Start the process. If the process with the same alias is already running, `start` will raise `ProcessExistsException`, while `ensure_running` will silently do nothing.

- `app_name`: application alias, given in the configuration
- `alias`: alias that will be given to actual started process. If `None`, application alias will be used
- `with_args`: list of additional arguments that will be added to the command
- `socket` can be specified for socket-type processes to set or override the name of UNIX socket file

`get_channel(self, alias)`

Returns the `Channel` object to communicate to the running process.

`terminate(self, alias)`

Terminates the process.

### Channel

`read(self)`

Performs a non-blocking read and returns any bytes available. Raises `EndpointClosedException` if the process on the other side of the channel is terminated.

`write(self, *data)`

Writes chunks of bytes to the channel. Raises `EndpointClosedException`.

`close(self)`

Closes the channel and frees up the resources.
