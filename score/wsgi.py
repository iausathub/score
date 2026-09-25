"""
WSGI config for score project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

import django
from django.core.wsgi import get_wsgi_application

from score.carto_debug import probe  # TEMP: CARTO_API_KEY diagnostics

probe("wsgi.py: top, before django.setup()")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "score.settings.development")
django.setup()

probe("wsgi.py: after django.setup()", check_setting=True)

application = get_wsgi_application()

probe("wsgi.py: after get_wsgi_application()", check_setting=True)
