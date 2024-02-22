from rest_framework import serializers

from repository.models import Location, Observation, Satellite


class SatelliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Satellite
        fields = ("sat_name", "sat_number", "constellation", "date_added")


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("obs_lat_deg", "obs_long_deg", "obs_alt_m", "date_added")


class ObservationSerializer(serializers.ModelSerializer):
    satellite_id = SatelliteSerializer(read_only=True)
    location_id = LocationSerializer(read_only=True)

    class Meta:
        model = Observation
        fields = (
            "id",
            "obs_time_utc",
            "obs_time_uncert_sec",
            "apparent_mag",
            "apparent_mag_uncert",
            "instrument",
            "obs_mode",
            "obs_filter",
            "obs_email",
            "obs_orc_id",
            "sat_ra_deg",
            "sat_ra_uncert_deg",
            "sat_dec_deg",
            "sat_dec_uncert_deg",
            "range_to_sat_km",
            "range_to_sat_uncert_km",
            "range_rate_sat_km_s",
            "range_rate_sat_uncert_km_s",
            "comments",
            "data_archive_link",
            "flag",
            "satellite_id",
            "location_id",
            "date_added",
        )
