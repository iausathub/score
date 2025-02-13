from django.utils import timezone

from repository.models import Observation


def filter_observations(form_data):
    """
    Filter observations based on the provided form data.

    This function applies various filters to the Observation queryset based on the
    fields provided in the form data. It supports filtering by satellite name, satellite
    number, observation mode, date range, observation ID, observer ORCID, MPC code,
    and international designator. Additionally, it can filter observations based on
    the observer's geographical location (latitude, longitude, and radius).

    Args:
        form_data (dict): A dictionary containing the form data with potential filter
            fields. The keys should match the expected filter fields, and the values
            should be the corresponding filter values.

    Returns:
        QuerySet: A Django QuerySet of Observation objects that match the applied
        filters. If no filters are provided, all observations are returned.
    """
    filters = {
        "sat_name": "satellite_id__sat_name__icontains",
        "sat_number": "satellite_id__sat_number",
        "obs_mode": "obs_mode__icontains",
        "observation_id": "id",
        "observer_orcid": "obs_orc_id__icontains",
        "mpc_code": "mpc_code",
        "intl_designator": "satellite_id__intl_designator",
        "instrument": "instrument__icontains",
    }

    observations = Observation.objects.all()

    # Handle date range filters separately to ensure timezone awareness
    start_date = form_data.get("start_date_range")
    end_date = form_data.get("end_date_range")

    if start_date:
        # Convert start date to datetime at start of day (00:00:00) with timezone
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        observations = observations.filter(obs_time_utc__gte=start_datetime)

    if end_date:
        # Convert end date to datetime at end of day (23:59:59) with timezone
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(end_date, timezone.datetime.max.time())
        )
        observations = observations.filter(obs_time_utc__lte=end_datetime)

    # Apply remaining filters
    for field, condition in filters.items():
        value = form_data.get(field)
        if value:
            observations = observations.filter(**{condition: value})

    if form_data.get("has_position_data"):
        observations = observations.filter(
            sat_ra_deg__isnull=False, sat_dec_deg__isnull=False
        )

    latitude = form_data.get("observer_latitude")
    longitude = form_data.get("observer_longitude")
    radius = form_data.get("observer_radius")

    if all([latitude, longitude, radius]):
        observations = [
            obs
            for obs in observations
            if obs.location_id.distance_to(latitude, longitude) <= radius
        ]

    return observations
