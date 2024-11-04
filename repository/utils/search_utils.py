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
        "start_date_range": "obs_time_utc__gte",
        "end_date_range": "obs_time_utc__lte",
        "observation_id": "id",
        "observer_orcid": "obs_orc_id__icontains",
        "mpc_code": "mpc_code",
        "intl_designator": "satellite_id__intl_designator",
        "instrument": "instrument__icontains",
    }

    observations = Observation.objects.all()
    for field, condition in filters.items():
        value = form_data.get(field)
        if value:
            observations = observations.filter(**{condition: value})

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
