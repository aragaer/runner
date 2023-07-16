# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Use dataclass instead of attr

### Fixed
- Removed Bettercodehub link

## [0.5.0] - 2018-10-26
### Changed
- Use channels 0.2.0 or higher

### Fixed
- Bettercodehub link in README
- 0.3.1 changes link in this changelog

## [0.4.0] - 2018-10-14
### Removed
- Channel-related code is moved to a separate package yet-another-io-channels-library

### Changed
- Runner now sleeps for 0.01 seconds when waiting for socket file

### Fixed
- Fixed for Python 3.4

## [0.3.1] - 2018-09-13
### Added
- get_fd() for channels
- Channels documentation
- TestChannel

### Fixed
- Arguments passed in run()/ensure_running() override arguments in config

## [0.3.0] - 2018-08-19
### Added
- BetterCodeHub badge
- PayPal donate button
- setpgrp flag
- line-buffering mode
- add() method

### Fixed
- Reading from closed channel now fails only when all data has been retrieved

### Removed
- Python 3.4 support

## [0.2.0] - 2018-08-17
### Added
- This changelog header
- Long description
- start() method

### Fixed
- Cleanup terminated processes
- Do not start process with ensure_running if it is already running

### Changed
- get_channel for terminated process now returns None

## [0.1.1] - 2018-01-28
### Added
- Travis CI badge in README
- Codecov badge in README
- Ignore "tests" in coverage report
- setup.py

### Fixed
- 'Unreleased' link in this changelog
- In runner tests wait result from processes for up to 0.1 seconds
- Runner didn't wait for unix socket

## 0.1.0 - 2018-01-28
### Added
- License
- Readme
- This changelog
- Runner class
- Channel class
- Handle stdio and socket channels

[Unreleased]: https://github.com/aragaer/runner/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/aragaer/runner/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/aragaer/runner/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/aragaer/runner/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/aragaer/runner/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/aragaer/runner/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/aragaer/runner/compare/v0.1.0...v0.1.1
