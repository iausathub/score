import re

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models
from django.utils import timezone


class Satellite(models.Model):

    sat_name = models.CharField(max_length=200)
    sat_number = models.IntegerField(default=0)
    date_added = models.DateTimeField("date added", default=timezone.now)

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
    obs_lat_deg = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    obs_long_deg = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    obs_alt_m = models.FloatField(default=0)
    date_added = models.DateTimeField("date added", default=timezone.now)

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
        if self.obs_alt_m < 0:
            raise ValidationError("Altitude must be greater than 0 meters.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Observation(models.Model):
    OBS_MODE_CHOICES = [
        ("VISUAL", "Visual"),
        ("BINOCULARS", "Binoculars"),
        ("CCD", "CCD"),
        ("CMOS", "CMOS"),
        ("OTHER", "Other"),
    ]

    obs_time_utc = models.DateTimeField("observation time")
    obs_time_uncert_sec = models.FloatField(default=0)
    apparent_mag = models.FloatField(null=True, blank=True)
    apparent_mag_uncert = models.FloatField(null=True, blank=True)
    instrument = models.CharField(max_length=200)
    obs_mode = models.CharField(max_length=200, choices=OBS_MODE_CHOICES)
    obs_filter = models.CharField(max_length=200)
    obs_email = models.TextField()
    obs_orc_id = ArrayField(models.CharField(max_length=19), default=list)
    sat_ra_deg = models.FloatField(default=0, null=True, blank=True)
    sat_dec_deg = models.FloatField(default=0, null=True, blank=True)
    sat_ra_dec_uncert_deg = ArrayField(
        models.FloatField(default=0, null=True, blank=True), null=True, blank=True
    )
    range_to_sat_km = models.FloatField(default=0, null=True, blank=True)
    range_to_sat_uncert_km = models.FloatField(default=0, null=True, blank=True)
    range_rate_sat_km_s = models.FloatField(default=0, null=True, blank=True)
    range_rate_sat_uncert_km_s = models.FloatField(default=0, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    data_archive_link = models.TextField(null=True, blank=True)
    flag = models.CharField(max_length=100, null=True, blank=True)
    satellite_id = models.ForeignKey(
        Satellite, on_delete=models.CASCADE, related_name="observations"
    )
    location_id = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="observations"
    )
    date_added = models.DateTimeField("date added", default=timezone.now)

    def __str__(self):
        return (
            str(self.id)
            + ", "
            + self.satellite_id.sat_name
            + ", "
            + str(self.obs_time_utc)
            + ", "
            + self.obs_email
        )

    class Meta:
        db_table = "observation"

    def clean(self):
        if not self.obs_time_utc:
            raise ValidationError("Observation time is required.")
        if self.obs_time_uncert_sec is None:
            raise ValidationError("Observation time uncertainty is required.")
        if self.obs_time_uncert_sec < 0:
            raise ValidationError("Observation time uncertainty must be positive.")
        if self.apparent_mag is not None and self.apparent_mag_uncert is None:
            raise ValidationError(
                "Apparent magnitude uncertainty is required if apparent magnitude is provided."  # noqa: E501
            )
        if self.apparent_mag is None and self.apparent_mag_uncert is not None:
            raise ValidationError(
                "Apparent magnitude must be provided if \
                                  uncertainty is provided."
            )
        if self.apparent_mag_uncert is not None and self.apparent_mag_uncert < 0:
            raise ValidationError("Apparent magnitude uncertainty must be positive.")
        if not self.obs_mode:
            raise ValidationError("Observation mode is required.")
        if self.obs_mode not in ["VISUAL", "BINOCULARS", "CCD", "CMOS", "OTHER"]:
            raise ValidationError(
                "Observation mode must be one of the following: VISUAL,\
                                  BINOCULARS, CCD, CMOS, OTHER"
            )
        if not self.obs_filter:
            raise ValidationError("Observation filter is required.")
        if not self.obs_email:
            raise ValidationError("Observer email is required.")
        if not re.match(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", self.obs_email
        ):
            raise ValidationError("Observer email is not correctly formatted.")
        if not self.instrument:
            raise ValidationError("Instrument is required.")
        if not self.obs_orc_id:
            raise ValidationError("Observer ORCID is required.")

        for id in self.obs_orc_id:
            if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", id):
                raise ValidationError("Observer ORCID not correctly formatted.")

        if self.sat_ra_deg and (self.sat_ra_deg < 0 or self.sat_ra_deg > 360):
            raise ValidationError("Right ascension must be between 0 and 360 degrees.")
        if self.sat_dec_deg and (self.sat_dec_deg < -90 or self.sat_dec_deg > 90):
            raise ValidationError("Declination must be between -90 and 90 degrees.")
        if self.sat_ra_dec_uncert_deg and (len(self.sat_ra_dec_uncert_deg) != 6):
            raise ValidationError(
                "RA/Dec uncertainty must be an array of \
                                  6 values (2x3 matrix)."
            )
        if self.range_to_sat_km and (self.range_to_sat_km < 0):
            raise ValidationError("Range to satellite must be positive.")
        if self.range_to_sat_uncert_km and (self.range_to_sat_uncert_km < 0):
            raise ValidationError("Range to satellite uncertainty must be positive.")
        if self.range_rate_sat_km_s and (self.range_rate_sat_km_s < 0):
            raise ValidationError("Range rate must be positive.")
        if self.range_rate_sat_uncert_km_s and (self.range_rate_sat_uncert_km_s < 0):
            raise ValidationError("Range rate uncertainty must be positive.")
        validate = URLValidator()

        if self.data_archive_link and not validate(self.data_archive_link):
            raise ValidationError("Data archive link is not correctly formatted.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
