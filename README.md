# QRADAR - WINDOWS SECURITY EVENT ID AUTOMATION

`qradar-wse-automation` retrieves Windows Security Events using the QRadar API, based on event IDs defined in the `data/windows_security_events.json` file. It constructs a SQL query dynamically, sends it to the API, parses the response, and creates or updates an issue in Redmine using an HTML template.

![Redmine Windows Security Event Issue](https://github.com/musaokankurtkaya/qradar-wse-automation/blob/main/assets/redmine_result.png)

## Table of Contents

- [Installation](#installation)
- [Execution / Usage](#execution--usage)

### Installation

#### Requirements

Before running the project, install the required Python packages:

```sh
$ pip install -r requirements.txt
```

#### Environment Configuration

Rename `.env.example` to `.env` and set the necessary keys:

- **QRadar SIEM settings**: Set `QRADAR_URL`, `QRADAR_USERNAME`, and `QRADAR_PASSWORD` to access the QRadar API. The other fields are optional.

- **Redmine settings**: Customize all fields as needed for your Redmine instance.

- **Teams workflow settings**: If you're using Microsoft Teams and have a workflow that posts to a channel when a webhook is received, you can enable message notifications to Teams.

### Execution / Usage

To run the project locally, open up a terminal and run the following command:

```sh
$ cd src/
$ python3 __main__.py
```

Or you can run it using Docker:

```sh
$ docker build -t qradar-wse-automation .
$ docker run qradar-wse-automation
```
