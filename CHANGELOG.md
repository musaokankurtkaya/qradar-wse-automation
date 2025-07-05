## [1.1.1](https://github.com/musaokankurtkaya/qradar-wse-automation) - 2025-07-05

### Added

- For each event in [windows_security_events.json](https://github.com/musaokankurtkaya/qradar-wse-automation/blob/main/src/data/windows_security_events.json) file, included_src_users, included_dst_users or included_groups parameters can be added to filter for only specific users or groups. If these parameters are not provided, all users and groups will be included and will check within excluded_src_users, excluded_dst_users and excluded_groups parameters. This change was made in the [QRadar.parse_searched_events](https://github.com/musaokankurtkaya/qradar-wse-automation/blob/main/src/services/qradar/qradar.py#L130) function.
- Sonar report has been added to the repository. You can check the report [here](https://github.com/musaokankurtkaya/qradar-wse-automation/blob/main/assets).

### Fixed

- load_qradar_config, load_redmine_config and load_windows_security_events functions' return type fixed for better type hinting.
- removed ".env.example" from ENV_FOLDER_PATH constant, it was not needed.
- In MsTeams.send_message class function, send_on_prod parameter changed with send_on_dev. Normally, teams messages are sending on prod mode but sometimes can be used in dev mode for testing purposes. For this reason, the parameter name has been changed to be more descriptive.
- While checking issue's journals in Redmine.upsert_wse_event was using with lambda, changed with list comprehension for more readable code.
- qradar query was using in app.py file as a string, this query moved to the .env file as QRADAR_QUERY variable. This way, it can be easily changed without modifying the code. The query is still formatted with only event_ids parameter, other parameters (interval and limit) are used as interpolated variables in the query.

## [1.0.0](https://github.com/musaokankurtkaya/qradar-wse-automation) - 2025-07-05

### Added

- Initial release