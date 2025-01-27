from datetime import datetime
from typing import Optional

from django.db.models import Avg, Count, Max, Min
from django.shortcuts import get_object_or_404
from ninja import Field, ModelSchema, NinjaAPI
from ninja.pagination import paginate
from ninja.throttling import AnonRateThrottle

from .models import Observation, Satellite

api = NinjaAPI(
    title="SCORE API",
    description="API for searching and accessing satellite observation data",
    version="1.0.0",
    throttle=[
        AnonRateThrottle("10/s"),
    ],
)


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
        ]


class SatelliteSchema(ModelSchema):
    class Meta:
        model = Satellite
        fields = ["sat_number", "sat_name", "date_added"]


@api.get("/observation/{observation_id}", response=ObservationSchema)
def get_observation(request, observation_id: int):
    """Get Observation Details

    Retrieve detailed information about a specific observation by its ID.

    ### Parameters
    - **observation_id**: The unique identifier of the observation

    ### Returns
    ObservationSchema containing:
    - Basic observation details (time, uncertainties)
    - Position measurements (RA, Dec, range, range rate)
    - Observer information (instrument, mode, filter)
    - Location data (latitude, longitude, altitude)
    - Associated satellite information

    ### Raises
    - **404**: Observation not found
    """
    return get_object_or_404(
        Observation.objects.select_related("location_id", "satellite_id"),
        id=observation_id,
    )


@api.get("/observations", response=list[ObservationSchema])
@paginate
def get_all_observations(request):
    """Get All Observations

    Retrieve all observations with pagination support.

    ### Parameters
    - **offset**: Page number (default: 1)
    - **limit**: Items per page (default: 1000)

    ### Returns
    Paginated response containing:
    - **items**: List of observations for current page
    - **count**: Total number of observations
    """
    return (
        Observation.objects.select_related("location_id", "satellite_id")
        .order_by("id")
        .all()
    )


@api.get("/satellite/{satellite_number}/observations", response=list[ObservationSchema])
def get_observations_for_satellite(request, satellite_number: int):
    """Get Satellite Observations

    Retrieve all observations for a specific satellite.

    ### Parameters
    - **satellite_number**: NORAD ID of the satellite

    ### Returns
    List of observations containing:
    - Position measurements (RA, Dec, range)
    - Brightness measurements (apparent magnitude)
    - Observation metadata (time, location, instrument, observer)
    """
    return Observation.objects.select_related("location_id", "satellite_id").filter(
        satellite_id__sat_number=satellite_number
    )


@api.get("/satellite/{satellite_number}", response=SatelliteSchema)
def get_satellite(request, satellite_number: int):
    """Get a single satellite by number

    Parameters
    ----------
    satellite_number (int): NORAD ID of the satellite

    Returns
    ----------
    SatelliteSchema: A schema containing satellite details
    """
    satellite = get_object_or_404(Satellite, sat_number=satellite_number)
    return SatelliteSchema.model_validate(satellite).model_dump()


@api.get("/search", response=list[ObservationSchema])
def search_observations(
    request,
    satellite_number: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_magnitude: Optional[float] = None,
    max_magnitude: Optional[float] = None,
):
    """Search Observations

    Search for observations using various filters.

    ### Parameters
    - **satellite_number**: Filter by NORAD ID
    - **start_date**: Include observations after this date (UTC)
    - **end_date**: Include observations before this date (UTC)
    - **min_magnitude**: Upper brightness limit (lower number = brighter)
    - **max_magnitude**: Lower brightness limit (higher number = dimmer)

    ### Returns
    List of observations matching the search criteria
    """
    query = Observation.objects.select_related("location_id", "satellite_id")

    if satellite_number:
        query = query.filter(satellite_id__sat_number=satellite_number)
    if start_date:
        query = query.filter(obs_time_utc__gte=start_date)
    if end_date:
        query = query.filter(obs_time_utc__lte=end_date)

    # Handle magnitude range
    if min_magnitude is not None and max_magnitude is not None:

        if min_magnitude < max_magnitude:
            print("Invalid range, returning empty list")
            return []
        query = query.filter(
            apparent_mag__lte=min_magnitude, apparent_mag__gte=max_magnitude
        )
    elif min_magnitude is not None:
        query = query.filter(apparent_mag__lte=min_magnitude)
    elif max_magnitude is not None:
        query = query.filter(apparent_mag__gte=max_magnitude)

    return query.all()


@api.get("/satellites", response=list[SatelliteSchema])
def list_satellites(
    request,
    name: Optional[str] = None,
):
    """List all satellites with optional name filter

    Parameters
    ----------
    name (optional): Filter by satellite name
    """

    query = Satellite.objects.all()
    if name:
        query = query.filter(sat_name__icontains=name)
    return query.all()


@api.get("/observations/recent", response=list[ObservationSchema])
def get_recent_observations(request, limit: int = 10):
    """Get most recent observations

    Parameters
    ----------
    limit: Number of observations to return
    """
    observations = Observation.objects.select_related(
        "location_id", "satellite_id"
    ).order_by("-obs_time_utc")[:limit]
    return observations


@api.get("/observations/stats", response=dict)
def get_observation_stats(request):
    """Get Observation Statistics

    Retrieve summary statistics about all observations.

    ### Returns
    Dictionary containing:
    - **total_observations**: Total number of observations
    - **total_satellites**: Total number of unique satellites
    - **time_range**: First and last observation dates
    - **magnitude_stats**: Average, brightest, and faintest magnitudes
    - **most_observed_satellites**: Top 5 most frequently observed satellites
    """
    # Basic counts
    total_obs = Observation.objects.count()
    total_satellites = Satellite.objects.count()

    # Time range
    time_stats = Observation.objects.aggregate(
        earliest_observation=Min("obs_time_utc"), latest_observation=Max("obs_time_utc")
    )

    # Magnitude stats
    mag_stats = Observation.objects.filter(apparent_mag__isnull=False).aggregate(
        avg_magnitude=Avg("apparent_mag"),
        brightest=Min("apparent_mag"),
        faintest=Max("apparent_mag"),
    )

    # Most observed satellites
    top_satellites = (
        Observation.objects.values("satellite_id__sat_number", "satellite_id__sat_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    return {
        "total_observations": total_obs,
        "total_satellites": total_satellites,
        "time_range": {
            "first": time_stats["earliest_observation"],
            "last": time_stats["latest_observation"],
        },
        "magnitude_stats": {
            "average": round(mag_stats["avg_magnitude"], 2)
            if mag_stats["avg_magnitude"]
            else None,
            "brightest": mag_stats["brightest"],
            "faintest": mag_stats["faintest"],
        },
        "most_observed_satellites": [
            {
                "number": sat["satellite_id__sat_number"],
                "name": sat["satellite_id__sat_name"],
                "observations": sat["count"],
            }
            for sat in top_satellites
        ],
    }
