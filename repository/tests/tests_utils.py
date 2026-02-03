import pytest
import requests
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils.general_utils import (
    get_norad_id,
    get_satellite_name,
    validate_position,
)
from repository.utils.search_utils import filter_observations


@pytest.fixture
def setup_data():
    obs_date = timezone.now()
    location = Location.objects.create(
        obs_lat_deg=33,
        obs_long_deg=-117,
        obs_alt_m=100,
        date_added=timezone.now(),
    )
    satellite = Satellite.objects.create(
        sat_name="STARLINK-123",
        sat_number=12345,
        date_added=timezone.now(),
    )
    observation = Observation.objects.create(
        obs_time_utc=obs_date,
        obs_email="abc@def.com",
        satellite_id=satellite,
        location_id=location,
        date_added=obs_date,
        obs_time_uncert_sec=5,
        apparent_mag=5.2,
        apparent_mag_uncert=0.1,
        obs_mode="VISUAL",
        obs_filter="CLEAR",
        instrument="none",
        obs_orc_id=["0123-4567-8910-1112"],
    )
    return location, satellite, observation


@pytest.mark.django_db
def test_validate_position(requests_mock, setup_data):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/ephemeris/catalog-number/",
        status_code=200,
        json={
            "data": [
                [
                    "TestSat",
                    "",
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "2024-02-20 00:36:13 UTC",
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "10",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "2024-02-20 00:36:13 UTC",
                ]
            ]
        },
    )
    response = requests.get(
        "https://satchecker.cps.iau.org/ephemeris/catalog-number/", timeout=5
    )
    result = validate_position(response, "TestSat", "2024-02-22T04:09:38.150")
    assert result


@pytest.mark.django_db
def test_validate_position_invalid_sat_name(requests_mock, setup_data):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/ephemeris/catalog-number/",
        status_code=200,
        json={
            "data": [
                [
                    "TestSat",
                    "",
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "2024-02-20 00:36:13 UTC",
                    "",  # noqa: B033
                    "",  # noqa: B033
                    "10",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "2024-02-20 00:36:13 UTC",
                ]
            ]
        },
    )
    response = requests.get(
        "https://satchecker.cps.iau.org/ephemeris/catalog-number/", timeout=5
    )
    result = validate_position(response, "InvalidSat", "2024-05-22T04:09:38.150")

    assert result == "Satellite name and number do not match"


@pytest.mark.django_db
def test_validate_position_not_visible(requests_mock, setup_data):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/ephemeris/catalog-number/?catalog=1",
        status_code=200,
        json={
            "api_source": "IAU CPS SatChecker",
            "info": "No position information found with this criteria",
            "version": "1.0",
        },
    )
    response = requests.get(
        "https://satchecker.cps.iau.org/ephemeris/catalog-number/?catalog=1",
        timeout=5,
    )
    result = validate_position(response, "TestSat", "2024-02-22T04:09:38.150")
    assert "Satellite with this ID not visible at this time and location" in result


@pytest.mark.django_db
def test_get_norad_id(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/norad-ids-from-name/",
        status_code=200,
        json={
            "data": [
                {
                    "norad_id": "12345",
                    "date_added": "2022-01-01 00:00:00 UTC",
                    "is_current_version": True,
                }
            ]
        },
    )

    result = get_norad_id("TestSat")
    assert result == "12345"


@pytest.mark.django_db
def test_get_norad_id_invalid_sat_name(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/norad-ids-from-name/",
        status_code=200,
        json={"data": []},
    )

    result = get_norad_id("InvalidSat")
    assert result is None, "Expected None when satellite name does not exist"


@pytest.mark.django_db
def test_get_norad_id_no_data(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/norad-ids-from-name/",
        status_code=200,
        json={"data": []},
    )

    result = get_norad_id("TestSat")
    assert result is None, "Expected None when no data is returned from API"


@pytest.mark.django_db
def test_get_norad_id_request_exception(requests_mock):
    # Mock the response from the API to raise a RequestException
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/norad-ids-from-name/",
        exc=requests.exceptions.RequestException,
    )

    result = get_norad_id("TestSat")
    assert result is None, "Expected None when a RequestException is raised"


@pytest.mark.django_db
def test_get_satellite_name(requests_mock):
    # Mock the response from the API (structure: count, data, source, version)
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/names-from-norad-id/",
        status_code=200,
        json={
            "count": 1,
            "data": [
                {
                    "name": "TestSat",
                    "is_current_version": True,
                }
            ],
            "source": "IAU CPS SatChecker",
            "version": "1.6.0",
        },
    )

    result = get_satellite_name("12345")
    assert result == "TestSat"


@pytest.mark.django_db
def test_get_satellite_name_invalid_norad_id(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/names-from-norad-id/",
        status_code=200,
        json={"count": 0, "data": []},
    )

    result = get_satellite_name("InvalidID")
    assert result is None, "Expected None when NORAD ID does not exist"


@pytest.mark.django_db
def test_get_satellite_name_no_data(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/names-from-norad-id/",
        status_code=200,
        json={"count": 0, "data": []},
    )

    result = get_satellite_name("12345")
    assert result is None, "Expected None when no data is returned from API"


@pytest.mark.django_db
def test_get_satellite_name_request_exception(requests_mock):
    # Mock the response from the API to raise a RequestException
    requests_mock.get(
        "https://satchecker.cps.iau.org/tools/names-from-norad-id/",
        exc=requests.exceptions.RequestException,
    )

    result = get_satellite_name("12345")
    assert result is None, "Expected None when a RequestException is raised"


@pytest.mark.django_db
def test_filter_observations_location(setup_data):
    location, satellite, observation = setup_data

    # Observation within radius
    form_data = {
        "observer_latitude": 33,
        "observer_longitude": -117,
        "observer_radius": 10,
    }
    results = filter_observations(form_data)
    assert len(results) == 1
    assert results[0] == observation

    # Observation outside radius
    form_data = {
        "observer_latitude": 34,
        "observer_longitude": -118,
        "observer_radius": 50,
    }
    results = filter_observations(form_data)
    assert len(results) == 0

    # No location filter
    form_data = {}
    results = filter_observations(form_data)
    assert len(results) == 1
    assert results[0] == observation

    # Partial location data (should not filter - error on form validation)
    form_data = {"observer_latitude": 33, "observer_longitude": -117}
    results = filter_observations(form_data)
    assert len(results) == 1
    assert results[0] == observation


@pytest.mark.django_db
def test_filter_observations_position_data(setup_data):
    location, satellite, observation = setup_data

    form_data = {"has_position_data": True}
    results = filter_observations(form_data)
    assert len(results) == 0

    form_data = {"has_position_data": False}
    results = filter_observations(form_data)
    assert len(results) == 1
    assert results[0] == observation
