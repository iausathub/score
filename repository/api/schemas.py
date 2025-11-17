from datetime import datetime
from typing import Literal
from uuid import UUID

from ninja import Field, ModelSchema, Schema
from pydantic import ConfigDict, EmailStr

from repository.models import Observation, Satellite


class ObservationSchema(ModelSchema):
    satellite_name: str = Field(None, alias="satellite_id.sat_name")
    satellite_number: int = Field(None, alias="satellite_id.sat_number")
    obs_lat_deg: float = Field(None, alias="location_id.obs_lat_deg")
    obs_long_deg: float = Field(None, alias="location_id.obs_long_deg")
    obs_alt_m: float = Field(None, alias="location_id.obs_alt_m")

    class Meta:
        model = Observation
        fields = [
            "id",
            "obs_time_utc",
            "obs_time_uncert_sec",
            "sat_ra_deg",
            "sat_dec_deg",
            "range_to_sat_km",
            "range_rate_sat_km_s",
            "apparent_mag",
            "apparent_mag_uncert",
            "instrument",
            "obs_mode",
            "obs_filter",
            "obs_orc_id",
            "sigma_2_ra",
            "sigma_2_dec",
            "sigma_ra_sigma_dec",
            "range_to_sat_uncert_km",
            "range_rate_sat_uncert_km_s",
            "comments",
            "data_archive_link",
            "limiting_magnitude",
            "mpc_code",
            # Additional satchecker fields
            "potentially_discrepant",
            "phase_angle",
            "range_to_sat_km_satchecker",
            "range_rate_sat_km_s_satchecker",
            "sat_ra_deg_satchecker",
            "sat_dec_deg_satchecker",
            "ddec_deg_s_satchecker",
            "dra_cosdec_deg_s_satchecker",
            "alt_deg_satchecker",
            "az_deg_satchecker",
            "sat_altitude_km_satchecker",
            "solar_elevation_deg_satchecker",
            "solar_azimuth_deg_satchecker",
            "illuminated",
        ]


class ObservationUploadSchema(Schema):
    # Required fields
    obs_time_utc: datetime
    obs_time_uncert_sec: float = Field(..., ge=0)
    instrument: str
    obs_mode: Literal["VISUAL", "BINOCULARS", "CCD", "CMOS", "OTHER"]
    obs_filter: str
    obs_email: EmailStr = Field(..., description="Email address of the observer")
    obs_orc_id: list[str] = Field(default_factory=list)
    # Can be None for a non-detection
    apparent_mag: float | None = None
    apparent_mag_uncert: float | None = Field(None, ge=0)
    limiting_magnitude: float = Field(..., gt=0)
    satellite_number: int = Field(..., description="NORAD ID")
    obs_lat_deg: float = Field(..., ge=-90, le=90)
    obs_long_deg: float = Field(..., ge=-180, le=180)
    obs_alt_m: float = 0

    # Optional observation data
    satellite_name: str | None = None
    sat_ra_deg: float | None = Field(None, ge=0, le=360)
    sat_dec_deg: float | None = Field(None, ge=-90, le=90)
    sigma_2_ra: float | None = None
    sigma_2_dec: float | None = None
    sigma_ra_sigma_dec: float | None = None
    range_to_sat_km: float | None = Field(None, ge=0)
    range_to_sat_uncert_km: float | None = Field(None, ge=0)
    range_rate_sat_km_s: float | None = None
    range_rate_sat_uncert_km_s: float | None = None
    comments: str | None = None
    data_archive_link: str | None = None
    mpc_code: str | None = None


class SatelliteSchema(ModelSchema):
    class Meta:
        model = Satellite
        fields = ["sat_number", "sat_name", "date_added"]


class ObservationListSchema(Schema):
    """Schema for returning a list of observations (responses)"""

    observations: list[ObservationSchema]


class ObservationBatchUploadSchema(Schema):
    """Schema for uploading multiple observations at once"""

    observations: list[ObservationUploadSchema]
    notification_email: EmailStr = Field(
        ...,
        description="Email address for confirmation, "
        "defaults to the email in the first observation if not provided",
    )
    send_confirmation: bool = Field(
        True, description="Whether to send confirmation email"
    )
    batch_id: UUID | None = Field(
        None,
        description="Optional batch ID for the upload. "
        "If not provided, one will be generated automatically",
    )


class UploadResponseSchema(Schema):
    batch_id: UUID
    status: str
    created_at: datetime


class SummarySchema(Schema):
    total: int
    created: int
    duplicates: int
    rejected: int


class ErrorSchema(Schema):
    model_config = ConfigDict(exclude_none=True)

    message: str
    code: int | None = None
    summary: SummarySchema | None = None


class RejectedObservationSchema(Schema):
    index: int
    sat_name: str
    sat_number: int
    obs_time_utc: datetime
    error: str


class ProgressSchema(Schema):
    total: int
    processed: int
    percent: int


class UploadProgressSchema(UploadResponseSchema):
    progress: ProgressSchema


class UploadCompletedWithErrorSchema(UploadResponseSchema):
    summary: SummarySchema
    rejected_obs: list[RejectedObservationSchema]


class UploadCompletedSchema(UploadResponseSchema):
    summary: SummarySchema


class UploadFailedSchema(UploadResponseSchema):
    model_config = ConfigDict(exclude_none=True)
    error: ErrorSchema
