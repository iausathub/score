from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("repository.urls")),
    path(settings.SECRET_ADMIN_TOKEN + "/admin/", admin.site.urls),
    path("celery-progress/", include("celery_progress.urls")),
] + debug_toolbar_urls()
