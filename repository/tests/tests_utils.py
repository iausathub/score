import pytest
import requests
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils.general_utils import (
    add_additional_data,
    below_line_of_sight,
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


def test_below_line_of_sight_visible_satellite():
    # Satellite well above the horizon is not below the line of sight.
    assert below_line_of_sight(45.0, 0.0) is False


def test_below_line_of_sight_rejects_far_below_horizon():
    # A satellite 42 deg below the horizon must be rejected for a ground observer
    # (0 km) and for a realistic elevation (100 m expressed as km).
    assert below_line_of_sight(-42.0, 0.0) is True
    assert below_line_of_sight(-42.0, 0.1) is True


def test_below_line_of_sight_negative_altitude_no_nan_passthrough():
    # Regression: a negative observer altitude used to make arccos return NaN,
    # and `-42 < NaN` silently evaluated False, letting the observation through.
    assert below_line_of_sight(-42.0, -0.1) is True
    assert below_line_of_sight(-42.0, -500.0) is True


def test_below_line_of_sight_missing_altitude_fails_safe():
    # An unparseable/NaN satellite altitude cannot be validated, so fail safe.
    assert below_line_of_sight(float("nan"), 0.0) is True


def test_add_additional_data_converts_meters_to_km(mocker):
    # Regression: the observation altitude arrives in meters (obs_alt_m) but the
    # line-of-sight geometry needs kilometers. add_additional_data must divide
    # by 1000 before handing the altitude to validate_position. Without this,
    # a below-horizon satellite could pass the visibility check.
    mocker.patch(
        "repository.utils.general_utils.requests.get",
        return_value=mocker.Mock(),
    )
    # Return a plain string so add_additional_data short-circuits after the
    # position check without needing a full SatChecker response to parse.
    mock_validate = mocker.patch(
        "repository.utils.general_utils.validate_position",
        return_value="checked",
    )

    add_additional_data(
        "TESTSAT",
        12345,
        "2024-06-01T00:00:00.000",  # after 2024-05-01 to skip the name lookup
        0.0,  # latitude
        0.0,  # longitude
        1000.0,  # altitude in METERS
    )

    # validate_position(response, name, obs_time, observer_altitude_km)
    observer_altitude_km = mock_validate.call_args.args[3]
    assert observer_altitude_km == pytest.approx(1.0)


@pytest.mark.django_db
def test_validate_position_below_horizon(requests_mock, setup_data):
    # SatChecker returns a position 42 deg below the horizon (e.g. from an
    # observer longitude entered without its minus sign): must be rejected.
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
                    "-42",
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
    assert "below horizon" in result


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
