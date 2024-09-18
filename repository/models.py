import re

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def validate_orcid(value):
    pattern = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{4}$")
    for orc_id in value:
        if not pattern.match(orc_id):
            raise ValidationError(f"{orc_id} is not a valid ORCID")


class Satellite(models.Model):

    sat_name = models.CharField(max_length=200, null=True, blank=True)
    sat_number = models.IntegerField(default=0)
    date_added = models.DateTimeField("date added", default=timezone.now)
    intl_designator = models.CharField(max_length=200, null=True, blank=True)
    launch_date = models.DateField(null=True, blank=True)
    decay_date = models.DateField(null=True, blank=True)
    rcs_size = models.CharField(max_length=200, null=True, blank=True)
    object_type = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.sat_number) + ", " + self.sat_name

    class Meta:
        db_table = "satellite"
        unique_together = ("sat_name", "sat_number")

    def clean(self):
        if not self.sat_number:
            raise ValidationError("Satellite number is required.")
        if len(str(self.sat_number)) > 6:
            raise ValidationError("NORAD ID must be 6 digits or less.")
        if int(self.sat_number) < 0:
            raise ValidationError("Satellite number must be positive.")

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
    obs_time_uncert_sec = models.FloatField(validators=[MinValueValidator(0)])
    apparent_mag = models.FloatField(null=True, blank=True)
    apparent_mag_uncert = models.FloatField(
        validators=[MinValueValidator(0)], null=True, blank=True
    )
    instrument = models.CharField(max_length=200)
    obs_mode = models.CharField(max_length=200, choices=OBS_MODE_CHOICES)
    obs_filter = models.CharField(max_length=200)
    obs_email = models.EmailField()
    obs_orc_id = ArrayField(
        models.CharField(max_length=19), default=list, validators=[validate_orcid]
    )
    sat_ra_deg = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(360)], null=True, blank=True
    )
    sat_dec_deg = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        null=True,
        blank=True,
    )
    sigma_2_ra = models.FloatField(null=True, blank=True)
    sigma_2_dec = models.FloatField(null=True, blank=True)
    sigma_ra_sigma_dec = models.FloatField(null=True, blank=True)
    range_to_sat_km = models.FloatField(
        validators=[MinValueValidator(0)], null=True, blank=True
    )
    range_to_sat_uncert_km = models.FloatField(
        validators=[MinValueValidator(0)], null=True, blank=True
    )
    range_rate_sat_km_s = models.FloatField(default=0, null=True, blank=True)
    range_rate_sat_uncert_km_s = models.FloatField(default=0, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    data_archive_link = models.URLField(null=True, blank=True)
    flag = models.CharField(max_length=100, null=True, blank=True)
    phase_angle = models.FloatField(null=True, blank=True)
    range_to_sat_km_satchecker = models.FloatField(null=True, blank=True)
    range_rate_sat_km_s_satchecker = models.FloatField(null=True, blank=True)
    sat_ra_deg_satchecker = models.FloatField(null=True, blank=True)
    sat_dec_deg_satchecker = models.FloatField(null=True, blank=True)
    ddec_deg_s_satchecker = models.FloatField(null=True, blank=True)
    dra_cosdec_deg_s_satchecker = models.FloatField(null=True, blank=True)
    alt_deg_satchecker = models.FloatField(null=True, blank=True)
    az_deg_satchecker = models.FloatField(null=True, blank=True)
    illuminated = models.BooleanField(null=True, blank=True)
    limiting_magnitude = models.FloatField(null=True, blank=True)
    mpc_code = models.CharField(max_length=10, null=True, blank=True)
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
        if self.apparent_mag is not None and self.apparent_mag_uncert is None:
            raise ValidationError(
                "Apparent magnitude uncertainty is required if "
                "apparent magnitude is provided."
            )
        if self.apparent_mag is None and self.apparent_mag_uncert is not None:
            raise ValidationError(
                "Apparent magnitude must be provided if \
                                  uncertainty is provided."
            )
        if self.obs_mode not in ["VISUAL", "BINOCULARS", "CCD", "CMOS", "OTHER"]:
            raise ValidationError(
                "Observation mode must be one of the following: VISUAL,\
                                  BINOCULARS, CCD, CMOS, OTHER"
            )
        if self.obs_orc_id and self.obs_orc_id[0] == "":
            raise ValidationError("ORCID cannot be empty.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
