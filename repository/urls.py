from django.conf import settings
from django.urls import include, path
from django.views.generic.base import RedirectView

from . import views
from .api import api

handler404 = views.custom_404


urlpatterns = [
    path("", views.index, name="root"),
    path("index/", RedirectView.as_view(url="/"), name="index"),
    path("data-format", views.data_format, name="data-format"),
    path("view", views.view_data, name="view-data"),
    path("download-all", views.download_all, name="download-all"),
    path("download-results", views.download_results, name="download-results"),
    path("search", views.search, name="search"),
    path("download-ids", views.download_obs_ids, name="download-obs-ids"),
    path(r"ht/" + settings.SECRET_HEALTH_CHECK_TOKEN, include("health_check.urls")),
    path("about", views.about, name="about"),
    path("download", views.download_data, name="download-data"),
    path("policy", views.policy, name="policy"),
    path(
        "last_observer_location/",
        views.last_observer_location,
        name="last_observer_location",
    ),
    path("data-change", views.data_change, name="data-change"),
    path("getting-started", views.getting_started, name="getting-started"),
    path("tools", views.tools, name="tools"),
    path("name-id-lookup", views.name_id_lookup, name="name-id-lookup"),
    path(
        "satellite-pos-lookup", views.satellite_pos_lookup, name="satellite-pos-lookup"
    ),
    path("generate-csv", views.generate_csv, name="generate-csv"),
    path(
        "satellite/<int:satellite_number>/",
        views.satellite_data_view,
        name="satellite-data-view",
    ),
    path("satellites", views.satellites, name="satellites"),
    path(
        "satellite/<int:satellite_number>/observations/",
        views.satellite_observations,
        name="satellite-observations",
    ),
    path(
        "observation/<int:observation_id>/",
        views.get_observation_by_id,
        name="get_observation_by_id",
    ),
    path("launch/<str:launch_number>/", views.launch_view, name="launch-view"),
    path("observer/<str:orc_id>/", views.observer_view, name="observer-view"),
    path(
        "observer/<str:orc_id>/observations/",
        views.observer_observations,
        name="observer-observations",
    ),
    path("api/", api.urls),
    path(
        "download-observer-data/",
        views.download_observer_data,
        name="download-observer-data",
    ),
]
