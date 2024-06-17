"""
Test Django settings for score project.
"""

from socket import gethostbyname, gethostname

from score.settings.base import get_secret  # noqa: F403

from .base import *  # noqa: F403

SECRET_KEY = get_secret("score-secret-key")["secret-key"]  # noqa: F405
SECRET_HEALTH_CHECK_TOKEN = get_secret("score-secret-key")[  # noqa: F405
    "health-check-token"
]  # noqa: F405
SECRET_ADMIN_TOKEN = get_secret("score-secret-key")["admin-token"]  # noqa: F405

ALLOWED_HOSTS = [get_secret("score-allowed-hosts")["score-prod-alb"]]  # noqa: F405
ALLOWED_HOSTS.append(gethostbyname(gethostname()))

CSRF_TRUSTED_ORIGINS = [
    get_secret("score-allowed-hosts")["score-prod-alb-csrf"]  # noqa: F405
]  # noqa: F405

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": get_secret("score_prod_db")["dbname"],  # noqa: F405
        "USER": get_secret("score_prod_db")["username"],  # noqa: F405
        "PASSWORD": get_secret("score_prod_db")["password"],  # noqa: F405
        "HOST": get_secret("score_prod_db")["host"],  # noqa: F405
        "PORT": get_secret("score_prod_db")["port"],  # noqa: F405
    },
}

EMAIL_HOST_USER = get_secret("score-settings")["server-email"]  # noqa: F405
EMAIL_HOST_PASSWORD = get_secret("score-settings")["temp-gmail-pw"]  # noqa: F405

SERVER_EMAIL = get_secret("score-settings")["server-email"]  # noqa: F405
ADMINS = get_secret("score-settings")["admins"]  # noqa: F405

RECAPTCHA_PUBLIC_KEY = get_secret("score-settings")["recaptcha-public"]  # noqa: F405
RECAPTCHA_PRIVATE_KEY = get_secret("score-settings")["recaptcha-private"]  # noqa: F405

AWS_STORAGE_BUCKET_NAME = get_secret("score-settings")[
    "static-bucket-name"
]  # noqa: F405
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
