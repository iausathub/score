from django.conf import settings
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("data-format", views.data_format, name="data-format"),
    path("view", views.view_data, name="view-data"),
    path("download-all", views.download_all, name="download-all"),
    path("download-results", views.download_results, name="download-results"),
    path("search", views.search, name="search"),
    path("upload", views.upload, name="upload-obs"),
    path("download-ids", views.download_obs_ids, name="download-obs-ids"),
    path(r"ht/" + settings.SECRET_HEALTH_CHECK_TOKEN, include("health_check.urls")),
    path("about", views.about, name="about"),
]
