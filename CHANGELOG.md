# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `GraphClient.get()` and path builders treat absolute `http(s)` URLs
  (including Graph `@odata.nextLink`) as complete request URLs. Joining a
  next-link onto `https://graph.microsoft.com/beta` produced Graph
  `ResourceNotFound` with `Invalid version: betahttps:`.

## [0.6.0] - TBD

### Changed

- Packaging metadata moved to `pyproject.toml` (static version).
- Release process uses `v*` git tags and a single GitHub Actions release workflow.

[Unreleased]: https://github.com/cdburkard/azol/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/cdburkard/azol/releases/tag/v0.6.0
