import pytest
import requests
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils import get_norad_id, get_satellite_name, validate_position


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
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/",
        status_code=200,
        json=[
            {
                "NAME": "TestSat",
                "ALTITUDE-DEG": "10",
                "TLE-DATE": "2024-02-20 00:36:13.000",
            }
        ],
    )
    response = requests.get(
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/", timeout=5
    )
    result = validate_position(response, "TestSat", "2024-02-22T04:09:38.150")
    assert result


@pytest.mark.django_db
def test_validate_position_invalid_sat_name(requests_mock, setup_data):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/",
        status_code=200,
        json=[
            {
                "NAME": "TestSat",
                "ALTITUDE-DEG": "10",
                "TLE-DATE": "2024-05-20 00:36:13",
            }
        ],
    )
    response = requests.get(
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/", timeout=5
    )
    result = validate_position(response, "InvalidSat", "2024-05-22T04:09:38.150")

    assert result == "Satellite name and number do not match"


@pytest.mark.django_db
def test_validate_position_not_visible(requests_mock, setup_data):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/",
        status_code=200,
        json=[],
    )
    response = requests.get(
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/", timeout=5
    )
    result = validate_position(response, "TestSat", "2024-02-22T04:09:38.150")
    assert result == "Satellite with this ID not visible at this time and location"


@pytest.mark.django_db
def test_get_norad_id(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/norad-ids-from-name/",
        status_code=200,
        json=[{"norad_id": "12345"}],
    )

    result = get_norad_id("TestSat")
    assert result == "12345"


@pytest.mark.django_db
def test_get_norad_id_invalid_sat_name(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/norad-ids-from-name/",
        status_code=200,
        json=[],
    )

    result = get_norad_id("InvalidSat")
    assert result is None, "Expected None when satellite name does not exist"


@pytest.mark.django_db
def test_get_norad_id_no_data(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/norad-ids-from-name/",
        status_code=200,
        json=[],
    )

    result = get_norad_id("TestSat")
    assert result is None, "Expected None when no data is returned from API"


@pytest.mark.django_db
def test_get_norad_id_request_exception(requests_mock):
    # Mock the response from the API to raise a RequestException
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/norad-ids-from-name/",
        exc=requests.exceptions.RequestException,
    )

    result = get_norad_id("TestSat")
    assert result is None, "Expected None when a RequestException is raised"


@pytest.mark.django_db
def test_get_satellite_name(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/names-from-norad-id/",
        status_code=200,
        json=[{"name": "TestSat"}],
    )

    result = get_satellite_name("12345")
    assert result == "TestSat"


@pytest.mark.django_db
def test_get_satellite_name_invalid_norad_id(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/names-from-norad-id/",
        status_code=200,
        json=[],
    )

    result = get_satellite_name("InvalidID")
    assert result is None, "Expected None when NORAD ID does not exist"


@pytest.mark.django_db
def test_get_satellite_name_no_data(requests_mock):
    # Mock the response from the API
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/names-from-norad-id/",
        status_code=200,
        json=[],
    )

    result = get_satellite_name("12345")
    assert result is None, "Expected None when no data is returned from API"


@pytest.mark.django_db
def test_get_satellite_name_request_exception(requests_mock):
    # Mock the response from the API to raise a RequestException
    requests_mock.get(
        "https://cps.iau.org/tools/satchecker/api/tools/names-from-norad-id/",
        exc=requests.exceptions.RequestException,
    )

    result = get_satellite_name("12345")
    assert result is None, "Expected None when a RequestException is raised"
