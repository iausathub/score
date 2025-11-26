from django.contrib import admin
from django.utils.html import format_html

from .models import APIKey, Location, Observation, Satellite


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
    search_fields = ["satellite_id__sat_name", "obs_email", "obs_mode", "date_added"]
    list_display = [
        "satellite_id",
        "obs_time_utc",
        "obs_email",
        "obs_mode",
        "apparent_mag",
        "date_added",
    ]
    list_filter = ["obs_time_utc", "obs_mode", "date_added"]


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    search_fields = ["name", "email", "key_prefix"]
    list_display = [
        "key_prefix_display",
        "name",
        "email",
        "status_display",
        "usage_count",
        "last_used_at",
        "created_at",
    ]
    list_filter = ["is_active", "created_at", "expires_at"]
    readonly_fields = [
        "key_hash",
        "key_prefix",
        "created_at",
        "last_used_at",
        "usage_count",
    ]
    fields = [
        "key_prefix",
        "name",
        "email",
        "is_active",
        "created_at",
        "expires_at",
        "last_used_at",
        "usage_count",
        "notes",
    ]

    def changelist_view(self, request, extra_context=None):
        """Add buttons to the changelist view for additional key management"""
        extra_context = extra_context or {}
        extra_context["create_key_url"] = "/admin-tools/api-keys/create/"
        extra_context["manage_keys_url"] = "/admin-tools/api-keys/"
        return super().changelist_view(request, extra_context=extra_context)

    def key_prefix_display(self, obj):
        """Display the key prefix"""
        return f"{obj.key_prefix}..."

    key_prefix_display.short_description = "Key Prefix"

    def status_display(self, obj):
        """Display status with color coding"""
        if obj.is_valid():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ Expired</span>'
            )

    status_display.short_description = "Status"

    def has_add_permission(self, request):
        """Disable adding keys through admin - use web interface instead"""
        return False
