from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import include, path
from django_ratelimit.exceptions import Ratelimited


def handler403(request, exception=None):
    """Custom 403 handler that returns 429 for rate limit errors.
    The django-ratelimit library returns a 403 status code by default"""
    if isinstance(exception, Ratelimited):
        return HttpResponse("Too many requests. Please try again later.", status=429)
    return HttpResponseForbidden("Forbidden")


urlpatterns = [
    path("", include("repository.urls")),
    path(settings.SECRET_ADMIN_TOKEN + "/admin/", admin.site.urls),
    path("celery-progress/", include("celery_progress.urls")),
] + debug_toolbar_urls()
