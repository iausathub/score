import pytest
import requests
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils import validate_position


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
        json=[{"NAME": "TestSat", "ALTITUDE-DEG": "10"}],
    )
    response = requests.get(
        "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/", timeout=5
    )
    result = validate_position(response, "InvalidSat", "2024-02-22T04:09:38.150")

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
