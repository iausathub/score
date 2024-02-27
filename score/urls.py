from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("repository.urls")),
    path(settings.SECRET_ADMIN_TOKEN + "/admin/", admin.site.urls),
]
