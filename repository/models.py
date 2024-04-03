from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models


class Satellite(models.Model):
    sat_name = models.CharField(max_length=200)
    sat_number = models.IntegerField(default=0)
    constellation = models.CharField(max_length=100, default="", null=True)
    date_added = models.DateTimeField("date added", default=datetime.now)

    def __str__(self):
        return self.sat_name

    class Meta:
        db_table = "satellite"

    def clean(self):
        if not self.sat_name:
            raise ValidationError("Satellite name is required.")
        if not self.sat_number:
            raise ValidationError("Satellite number is required.")
        if len(str(self.sat_number)) > 5:
            raise ValidationError("NORAD ID must be 5 digits or less.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Location(models.Model):
    obs_lat_deg = models.FloatField(default=0)
    obs_long_deg = models.FloatField(default=0)
    obs_alt_m = models.FloatField(default=0)
    date_added = models.DateTimeField("date added", default=datetime.now)

    def __str__(self):
        return (
            str(self.obs_lat_deg)
            + ", "
            + str(self.obs_long_deg)
            + ", "
            + str(self.obs_alt_m)
        )

    class Meta:
        db_table = "location"

    def clean(self):
        if not self.obs_lat_deg:
            raise ValidationError("Latitude is required.")
        if not self.obs_long_deg:
            raise ValidationError("Longitude is required.")
        if not self.obs_alt_m:
            raise ValidationError("Altitude is required.")
        if self.obs_lat_deg < -90 or self.obs_lat_deg > 90:
            raise ValidationError("Latitude must be between -90 and 90 degrees.")
        if self.obs_long_deg < -180 or self.obs_long_deg > 180:
            raise ValidationError("Longitude must be between -180 and 180 degrees.")
        if self.obs_alt_m < 0:
            raise ValidationError("Altitude must be greater than 0 meters.")


class Image(models.Model):
    image_name = models.TextField()
    image_path = models.TextField()
    date_added = models.DateTimeField("date added", default=datetime.now)

    def __str__(self):
        return self.image_name

    class Meta:
        db_table = "image"


class Observation(models.Model):
    obs_time_utc = models.DateTimeField("observation time")
    obs_time_uncert_sec = models.FloatField(default=0)
    apparent_mag = models.FloatField(default=0)
    apparent_mag_uncert = models.FloatField(default=0)
    instrument = models.CharField(max_length=200)
    obs_mode = models.CharField(max_length=200)
    obs_filter = models.CharField(max_length=200)
    obs_email = models.TextField()
    obs_orc_id = models.CharField(max_length=200, null=True)
    sat_ra_deg = models.FloatField(default=0, null=True)
    sat_ra_uncert_deg = models.FloatField(default=0, null=True)
    sat_dec_deg = models.FloatField(default=0, null=True)
    sat_dec_uncert_deg = models.FloatField(default=0, null=True)
    range_to_sat_km = models.FloatField(default=0, null=True)
    range_to_sat_uncert_km = models.FloatField(default=0, null=True)
    range_rate_sat_km_s = models.FloatField(default=0, null=True)
    range_rate_sat_uncert_km_s = models.FloatField(default=0, null=True)
    comments = models.TextField(null=True)
    data_archive_link = models.TextField(null=True)
    flag = models.CharField(max_length=100, null=True)
    satellite_id = models.ForeignKey(Satellite, on_delete=models.CASCADE)
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    image_id = models.ForeignKey(Image, on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField("date added", default=datetime.now)

    def __str__(self):
        return (
            str(self.obs_time_utc)
            + ", "
            + self.obs_email
            + ", "
            + self.satellite_id.sat_name
        )

    class Meta:
        db_table = "observation"

    def clean(self):
        if not self.obs_time_utc:
            raise ValidationError("Observation time is required.")
        if not self.obs_time_uncert_sec:
            raise ValidationError("Observation time uncertainty is required.")
        if not self.apparent_mag:
            raise ValidationError("Apparent magnitude is required.")
        if not self.apparent_mag_uncert:
            raise ValidationError("Apparent magnitude uncertainty is required.")
        if not self.obs_mode:
            raise ValidationError("Observation mode is required.")
        if not self.obs_filter:
            raise ValidationError("Observation filter is required.")
        if not self.obs_email:
            raise ValidationError("Observer email is required.")
        if not self.instrument:
            raise ValidationError("Instrument is required.")
        if not self.obs_orc_id:
            raise ValidationError("Observer ORCID is required.")
