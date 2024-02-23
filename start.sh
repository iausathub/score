#! /bin/bash

echo "${0}: running migrations."
python manage.py migrate

echo "${0}: starting server."
gunicorn -b 0.0.0.0 -w 2 score.wsgi:application
