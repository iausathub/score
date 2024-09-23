# Satellite Constellation Observation Repository (SCORE)

## Overview
SCORE is a centralized repository for satellite brightness and position observations. Users can upload and download satellite observation data (optical and visual measurements currently, and eventually corresponding images and radio related data as well). The application is currently in development and is not yet ready for public use.

- [Installation](#installation)
   * [Prerequisites](#prerequisites)
   * [Setup](#setup)
- [Tools](#tools)
- [Deployment & Infrastructure](#deployment-infrastructure)
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
10. Navigate to http://127.0.0.1:8000/ and try to upload the ```test_data.csv``` file from ```score/dev```.

11. Testing upload - if Python crashes and you get this error during observation file upload: ```Worker exited prematurely: signal 6 (SIGABRT) Job: 0.```, then you need to quit the Celery worker, run the command below, restart Terminal, then restart the Celery worker.
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```
To keep this from happening every time the machine restarts, add that line to your ~/.zshrc or ~/.bashrc file too.

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
Code pushed to SCORE's GitHub repository is mirrored to NOIRLab's GitLab repo, and deployed using the Dockerfiles in this repo using Kubernetes and AWS. 
Testing and linting are run as part of the GitHub actions on every commit, and a code coverage report is generated as part of a pull request. The main and develop branches are restricted so that only approved changes can kick off a deployment pipeline job.

<a name="license"></a>
## License
This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.
