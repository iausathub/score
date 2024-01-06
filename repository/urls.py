from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("data-format.html", views.data_format, name="data-format"),
    path("view.html", views.view_data, name="view-data"),
]