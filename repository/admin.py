from django.contrib import admin

from .models import Location, Observation, Satellite


@admin.register(Satellite)
class SatelliteAdmin(admin.ModelAdmin):
    search_fields = ["sat_name", "sat_number", "intl_designator"]
    list_display = ["sat_name", "sat_number", "intl_designator", "date_added"]
    list_filter = ["date_added"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ["obs_lat_deg", "obs_long_deg", "obs_alt_m"]
    list_display = ["obs_lat_deg", "obs_long_deg", "obs_alt_m", "date_added"]
    list_filter = ["date_added"]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    search_fields = ["satellite_id__sat_name", "obs_email", "obs_mode"]
    list_display = [
        "satellite_id",
        "obs_time_utc",
        "obs_email",
        "obs_mode",
        "apparent_mag",
    ]
    list_filter = ["obs_time_utc", "obs_mode"]
