import pytest
import requests
from django.urls import reverse
from django.utils import timezone

from repository.models import Location, Observation, Satellite

base_url = "https://score.dev.aws.noirlab.edu/api"


def make_request(endpoint):
    return requests.get(endpoint, timeout=120)


@pytest.fixture
@pytest.mark.django_db
def benchmark_data():
    # Create test satellite
    satellite = Satellite.objects.create(
        sat_name="STARLINK-TEST", sat_number=59588, date_added=timezone.now()
    )

    # Create test location
    location = Location.objects.create(
        obs_lat_deg=33, obs_long_deg=-117, obs_alt_m=100, date_added=timezone.now()
    )

    # Create multiple observations
    for i in range(1000):
        Observation.objects.create(
            obs_time_utc=timezone.now(),
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
            satellite_id=satellite,
            location_id=location,
            date_added=timezone.now(),
            obs_time_uncert_sec=5,
            apparent_mag=5.0 + (i % 10) * 0.1,
            apparent_mag_uncert=0.1,
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            instrument="none",
        )

    return satellite


def test_benchmark_api_observations(benchmark):
    # Test get all observations
    endpoint = f"{base_url}/observations"

    response = benchmark(make_request, endpoint)
    assert response.status_code == 200


def test_benchmark_api_satellite_observations(benchmark):
    # Test get all observations for a satellite
    endpoint = f"{base_url}/satellite/59588/observations"

    response = benchmark(make_request, endpoint)
    assert response.status_code == 200


@pytest.mark.django_db
def test_benchmark_satellite_query(benchmark, benchmark_data):
    # Test direct query of satellite observations
    def query_satellite_observations():
        satellite = benchmark_data
        observations = satellite.observations.all()
        return list(observations)

    result = benchmark(query_satellite_observations)
    assert len(result) == 1000


@pytest.mark.django_db
def test_benchmark_view_satellite_observations(benchmark, client, benchmark_data):
    # Test view with satellite observations
    satellite = benchmark_data
    url = reverse("satellite-observations", args=[satellite.sat_number])
    response = benchmark(lambda: client.get(url))
    assert response.status_code == 200
    assert response.json()["total"] == 1000
