from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("data-format.html", views.data_format, name="data-format"),
    path("view.html", views.view_data, name="view-data"),
    path("download-all", views.download_all, name="download-all"),
    path("download-results", views.download_results, name="download-results"),
    path("search.html", views.search, name="search"),
]
