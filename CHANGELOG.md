## [1.0.1](https://github.com/musaokankurtkaya/qradar-wse-automation) - 2026-09-18

### Added

- Configurable `QRADAR_MAX_SEARCH_QUERY_INTERVAL`, `QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS`, and `QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_DELAY` environment variables
- `QRADAR_SEARCH_QUERY_LIMIT` support with a default of 9999

### Changed

- Renamed `SMTP_Config` to `SMTPConfig`
- Renamed QRadar query settings: `QRADAR_AQL_SEARCH_QUERY` → `QRADAR_SEARCH_QUERY`, `QRADAR_QUERY_INTERVAL` → `QRADAR_SEARCH_QUERY_INTERVAL`, `QRADAR_QUERY_LIMIT` → `QRADAR_SEARCH_QUERY_LIMIT`
- Made `QRADAR_SEARCH_QUERY_INTERVAL` required
- Inject `{wse_ids}`, `{interval}`, and `{limit}` into the search query via Python format placeholders
- Treat empty environment values as unset during config validation

### Removed

- Unused `python-redmine` dependency

## [1.0.0](https://github.com/musaokankurtkaya/qradar-wse-automation) - 2026-09-14

### Added

- Initial release
