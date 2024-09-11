"""
Base Django settings for score project.
"""

import json
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def get_secret_env(secret_name):

    if secret_name == "score_prod_db":  # noqa: S105
        score_prod_db = {
            "dbname": os.environ.get("DB_NAME"),
            "username": os.environ.get("DB_USERNAME"),
            "password": os.environ.get("DB_PASSWORD"),
            "host": os.environ.get("DB_HOST"),
            "port": os.environ.get("DB_PORT"),
        }

        return score_prod_db

    if secret_name == "score-settings":  # noqa: S105
        score_settings = {
            "recaptcha-public": os.environ.get("RECAPTCHA_PUBLIC_KEY"),
            "recaptcha-private": os.environ.get("RECAPTCHA_PRIVATE_KEY"),
            "server-email": os.environ.get("EMAIL_HOST_USER"),
            "temp-gmail-pw": os.environ.get("EMAIL_HOST_PASSWORD"),
            "admins": os.environ.get("ADMINS"),
        }

        return score_settings

    if secret_name == "score-secret-key":  # noqa: S105
        score_secret_key = {
            "secret-key": os.environ.get("SECRET_KEY"),
            "health-check-token": os.environ.get("SECRET_HEALTH_CHECK_TOKEN"),
            "admin-token": os.environ.get("SECRET_ADMIN_TOKEN"),
        }

        return score_secret_key

    if secret_name == "score-allowed-hosts":  # noqa: S105
        score_allowed_hosts = {  # noqa: F841
            "score-prod-alb-csrf": os.environ.get("CSRF_TRUSTED_ORIGINS"),
            "score-prod-alb": os.environ.get("ALLOWED_HOSTS"),
        }


def get_secret(secret_name):

    # conditionally get secret from environment variables if they exist
    if os.environ.get("SECRET_KEY") is not None:
        return get_secret_env(secret_name)

    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    get_secret_value_response = None
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        print(e)
        raise e

    if get_secret_value_response is None:
        raise Exception("No secret value response")
    secrets = json.loads(get_secret_value_response["SecretString"])

    return secrets


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production.
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = True

# Application definition

INSTALLED_APPS = [
    "repository.apps.RepositoryConfig",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "compressor",
    "rest_framework",
    "health_check",
    "health_check.db",
    "health_check.storage",
    "health_check.contrib.migrations",
    "celery",
    "celery_progress",
    "anymail",
    "django_recaptcha",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "score.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "score.wsgi.application"

# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = None


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = os.path.join(BASE_DIR, "static/")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "score/static"),
]
STATIC_ROOT = "score/static"
print(f"static root: {STATIC_ROOT}")
print(f"static url: {STATIC_URL}")
print(f"static dirs: {STATICFILES_DIRS}")


STATICFILES_FINDERS = [
    "compressor.finders.CompressorFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Celery settings
BROKER_URL = "redis://localhost"
CELERY_RESULT_BACKEND = "redis://localhost"
CELERY_RESULT_SERIALIZER = "json"

"""
EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend" # for use with non-gmail email
ANYMAIL = {
    "SENDGRID_API_KEY": get_secret("score-settings")["sendgrid-api-key"],
}
"""

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

JAZZMIN_SETTINGS = {
    "site_title": "SCORE Admin",
    "site_header": "SCORE Admin",
    "site_brand": "SCORE",
}
