"""
ASGI config for score project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from score.carto_debug import probe  # TEMP: CARTO_API_KEY diagnostics

probe("asgi.py: top")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "score.settings.development")

application = get_asgi_application()

probe("asgi.py: after get_asgi_application()", check_setting=True)
