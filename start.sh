#! /bin/bash

echo "${0}: running migrations."
python manage.py migrate

echo "${0}: collecting static files."
python manage.py collectstatic --noinput

echo "${0}: starting server."
ENV DJANGO_SETTINGS_MODULE=$1
gunicorn -b 0.0.0.0 -w 2 score.wsgi:application
