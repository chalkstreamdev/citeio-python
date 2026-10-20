# Changelog

All notable changes to citeio are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-20

Checked against one live Predictable report from cite.io. Install from the `v0.1.0` tag.

### Added

- `Client`: an API client on the standard library. It lists one project's reports (50 rows per page, with duplicate ids removed across pages), gets one report, and downloads an image. A non-2xx response raises `APIError`.
- `body_html`: renders a report's `presentation` paragraphs as `<p>` elements, with external citations as links and internal citations as links to your own URLs.
- `sources_html`: renders the Sources list as a `<ul>`.
- `publishable`: the grade rule, where a null grade means ungraded, not bad.
- `parse_datetime`: reads the API's ISO 8601 timestamps as aware UTC datetimes.

[Unreleased]: https://github.com/chalkstreamdev/citeio-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chalkstreamdev/citeio-python/releases/tag/v0.1.0
