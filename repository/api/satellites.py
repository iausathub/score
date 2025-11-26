from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from ..models import Observation, Satellite
from .schemas import ObservationSchema, SatelliteSchema

router = Router()


@router.get("/", response=list[SatelliteSchema])
def list_satellites(
    request,
    name: str | None = None,
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


@router.get("/{satellite_number}/observations", response=list[ObservationSchema])
@paginate
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


@router.get("/{satellite_number}", response=SatelliteSchema)
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
