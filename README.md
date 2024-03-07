# Satellite Constellation Observation Repository (SCORE)

## Overview
SCORE is a centralized repository for satellite brightness and position observations. Users can upload and download satellite observation data (optical and visual measurements currently, and eventually corresponding images and radio related data as well). The application is currently in development and is not yet ready for public use.

- [Installation](#installation)
   * [Prerequisites](#prerequisites)
   * [Setup](#setup)
- [Tools](#tools)
- [Deployment & Infrastructure](#deployment-infrastructure)
- [Sample Data](#sample-data)
- [License](#license)

<a name="installation"></a>
## Installation

<a name="dependencies"></a>
### Dependencies/Prerequisites
* Python 3.11.4+
* Django 4.0.10+
* PostgreSQL 15.5+
* Celery 5.3.6+
* Redis 7.2+
* PGAdmin (optional, for viewing postgres database)

<a name="setup"></a>
### Setup
1. Navigate to the directory where you want to install SCORE and clone the repo:
```bash
git clone https://github.com/iausathub/score.git
```
2. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install the requirements:
```bash
cd api
pip install -r requirements.txt
```
4. Install Redis following the directions here: https://redis.io/docs/install/install-redis/ and start the server
5. Create a database called "score_test" in your local PostgreSQL server.
6. Run the database and static files setup steps:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```
7. Create a superuser:
```bash
python manage.py createsuperuser
```
8. Start a Celery worker:
```bash
celery -A score worker --loglevel=info
```
9. Start the Django server:
```bash
python manage.py runserver
```
10. Navigate to http://127.0.0.1:8000/.

<a name="tools"></a>
## Tools

Right now the code is set up to use [Black](https://black.readthedocs.io/en/stable/) for code formatting and [Ruff](https://docs.astral.sh/ruff/) for linting with the following rules turned on:
* E (pycodestyle errors)
* F (Pyflakes)
* I (isort)
* N (pep8-naming)
* UP (pyupgrade)
* S (flake8-bandit)
* B (flake8-bugbear)

Ruff and Black can be set up to run as pre-commit hooks, but they are also run on every push to a branch in the run_tests.yml workflow (which also runs all the tests)

<a name="deployment-infrastructure"></a>
## Deployment & Infrastructure

[AWS Services](dev/score_AWS_services.drawio.png)

<a name="sample-data"></a>
## Sample Data
1. To generate sample data for testing upload, run the following from the main "score" directory:
```bash
python generate_test_csv.py
```
2. This will create a file called "test_observations.csv" in the main "score" directory. You can then upload this file on the main page of the app.
3. You will also need to disable the `validate_position` check in `utils.py`. If not, SCORE will attempt
to use SatChecker to validate the data (which will fail).

<a name="license"></a>
## License
[![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
