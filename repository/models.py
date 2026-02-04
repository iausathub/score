import hashlib
import logging
import re
import secrets
import uuid
from datetime import timedelta
from math import atan2, cos, radians, sin, sqrt

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def validate_orcid(value):
    pattern = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]$")
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

    class Meta:
        db_table = "location"

    def __str__(self):
        return (
            str(self.obs_lat_deg)
            + ", "
            + str(self.obs_long_deg)
            + ", "
            + str(self.obs_alt_m)
        )

    def distance_to(self, lat, lon):
        earth_radius = 6371  # Earth's radius in kilometers

        lat1, lon1 = radians(self.obs_lat_deg), radians(self.obs_long_deg)
        lat2, lon2 = radians(lat), radians(lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_radius * c

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation is called
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
    potentially_discrepant = models.BooleanField(default=False, null=True, blank=True)
    phase_angle = models.FloatField(null=True, blank=True)
    range_to_sat_km_satchecker = models.FloatField(null=True, blank=True)
    range_rate_sat_km_s_satchecker = models.FloatField(null=True, blank=True)
    sat_ra_deg_satchecker = models.FloatField(null=True, blank=True)
    sat_dec_deg_satchecker = models.FloatField(null=True, blank=True)
    ddec_deg_s_satchecker = models.FloatField(null=True, blank=True)
    dra_cosdec_deg_s_satchecker = models.FloatField(null=True, blank=True)
    alt_deg_satchecker = models.FloatField(null=True, blank=True)
    az_deg_satchecker = models.FloatField(null=True, blank=True)
    sat_altitude_km_satchecker = models.FloatField(null=True, blank=True)
    solar_elevation_deg_satchecker = models.FloatField(null=True, blank=True)
    solar_azimuth_deg_satchecker = models.FloatField(null=True, blank=True)
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
        indexes = [
            models.Index(fields=["satellite_id", "obs_time_utc"]),  # ASC
            models.Index(fields=["satellite_id", "-obs_time_utc"]),  # DESC
        ]

    def clean(self):
        if self.apparent_mag is not None and self.apparent_mag_uncert is None:
            raise ValidationError(
                "Apparent magnitude uncertainty is required if "
                "apparent magnitude is provided."
            )
        if self.apparent_mag is None and self.apparent_mag_uncert is not None:
            raise ValidationError("Apparent magnitude must be provided if \
                                  uncertainty is provided.")
        if self.obs_mode not in ["VISUAL", "BINOCULARS", "CCD", "CMOS", "OTHER"]:
            raise ValidationError(
                "Observation mode must be one of the following: VISUAL,\
                                  BINOCULARS, CCD, CMOS, OTHER"
            )
        if self.obs_orc_id and self.obs_orc_id[0] == "":
            raise ValidationError("ORCID cannot be empty.")

        # Normalize ORCIDs
        if self.obs_orc_id:
            self.obs_orc_id = [
                orc_id.upper() if orc_id else orc_id for orc_id in self.obs_orc_id
            ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class APIKey(models.Model):
    """
    API Key model for authenticating API requests.

    Keys are generated using secure random tokens and stored hashed in the database.
    Each key can have an optional expiration date and can be revoked.
    """

    KEY_LENGTH = 32
    PREFIX_LENGTH = 8  # characters to show as prefix

    key_hash = models.CharField(max_length=128, unique=True, db_index=True)

    # identification without revealing full key
    key_prefix = models.CharField(max_length=PREFIX_LENGTH, db_index=True)

    name = models.CharField(
        max_length=200, help_text="Name of the API key holder (person or organization)"
    )
    orcid_id = models.CharField(max_length=19, help_text="ORCID ID of the key holder")
    email = models.EmailField(help_text="Contact email for the key holder")

    # Key lifecycle
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Optional expiration date for the key"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether the key is currently active"
    )

    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(
        default=0, help_text="Number of times this key has been used"
    )

    # Additional metadata
    notes = models.TextField(blank=True, help_text="Internal notes about this key")

    class Meta:
        db_table = "api_key"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "expires_at"]),
        ]
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @classmethod
    def generate_key(cls):
        """Generate a secure random API key."""
        return secrets.token_urlsafe(cls.KEY_LENGTH)

    @staticmethod
    def hash_key(key: str) -> str:
        """
        Hash an API key for secure storage using SHA-256.
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def is_valid(self) -> bool:
        """Check if the key is valid (active and not expired)."""
        if not self.is_active:
            return False
        if self.expires_at is not None and timezone.now() > self.expires_at:
            return False
        return True

    def record_usage(self):
        """
        Record that this key was used.
        """
        self.last_used_at = timezone.now()
        self.usage_count += 1
        try:
            self.save(update_fields=["last_used_at", "usage_count"])
        except Exception as e:
            # Don't fail authentication if usage tracking fails
            logger.warning(f"Failed to record API key usage: {e}")

    def revoke(self):
        """Revoke this API key and log the action."""
        self.is_active = False
        self.save(update_fields=["is_active"])
        logger.info(
            f"API key revoked: {self.key_prefix}... "
            f"(name={self.name}, email={self.email})"
        )

    @classmethod
    def create_key(
        cls,
        name: str,
        email: str,
        orcid_id: str,
        expires_in_days: int | None = None,
        notes: str = "",
    ):
        """
        Create a new API key.

        Returns:
            tuple: (api_key_instance, plaintext_key)

        Note: The plaintext key should be returned to the user immediately
        and will not be recoverable after this method returns.
        """
        plaintext_key = cls.generate_key()
        key_hash = cls.hash_key(plaintext_key)
        key_prefix = plaintext_key[: cls.PREFIX_LENGTH]

        expires_at = None
        if expires_in_days is not None:
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        api_key = cls.objects.create(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            email=email,
            orcid_id=orcid_id,
            expires_at=expires_at,
            notes=notes,
        )

        logger.info(
            f"API key created: {key_prefix}... "
            f"(name={name}, email={email}, "
            f"expires={'Never' if expires_at is None else expires_at.date()})"
        )

        return api_key, plaintext_key

    @classmethod
    def validate_key(cls, plaintext_key: str):
        """
        Validate a plaintext API key and return the corresponding APIKey object.

        Returns:
            APIKey object if valid, None otherwise
        """
        if not plaintext_key:
            logger.warning("API key validation failed: Empty key provided")
            return None

        # Hash the provided key
        provided_hash = cls.hash_key(plaintext_key)

        try:
            api_key = cls.objects.get(key_hash=provided_hash)

            # Validate the hash
            if not secrets.compare_digest(api_key.key_hash, provided_hash):
                logger.warning("API key validation failed: Hash mismatch")
                return None

            # Check if key is valid (active and not expired)
            if api_key.is_valid():
                return api_key
            else:
                logger.warning(
                    f"API key validation failed: Key inactive or expired "
                    f"(prefix={api_key.key_prefix}..., active={api_key.is_active}, "
                    f"expires={api_key.expires_at})"
                )
                return None

        except cls.DoesNotExist:
            logger.warning("API key validation failed: Key not found")
            return None


class APIKeyVerification(models.Model):
    """
    API Key verification model for verifying the user's identity.
    """

    email = models.EmailField(help_text="Contact email for the key holder")
    name = models.CharField(max_length=200, help_text="Name of the key holder")
    orcid_id = models.CharField(max_length=19, help_text="ORCID ID of the key holder")

    verification_token = models.UUIDField(
        default=uuid.uuid4, help_text="Verification token"
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_key_verification"
        ordering = ["-created_at"]
        verbose_name = "API Key Verification"
        verbose_name_plural = "API Key Verifications"

    def is_active(self) -> bool:
        """Check if the verification is active (not expired)."""
        if self.expires_at is not None and timezone.now() > self.expires_at:
            return False
        return True
