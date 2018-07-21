# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- This changelog header

### Fixed
- Cleanup terminated processes

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

[Unreleased]: https://github.com/aragaer/runner/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/aragaer/runner/compare/v0.1.0...v0.1.1
