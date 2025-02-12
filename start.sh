#! /bin/bash

echo "${0}: running migrations."
python manage.py migrate

echo "${0}: collecting static files."
python manage.py collectstatic --noinput

python manage.py compress --force

# Kubernetes specific:
# Copy Django generated static files to `/shared-files` if it exists.
# An adjacent container running NGINX will serve these files as it also
# mounts the shared files directory.
if [ -d "/shared-files" ]; then
	cp -r /usr/src/app/static /shared-files/
fi

echo "${0}: starting server."
ENV DJANGO_SETTINGS_MODULE=$1
gunicorn -b 0.0.0.0 -w 2 --timeout 120 score.wsgi:application
