import os

from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from repository.api import api
from repository.models import Location, Observation, Satellite


class TestAPI(TestCase):
    def setUp(self):
        os.environ["NINJA_SKIP_REGISTRY"] = "1"
        self.client = TestClient(api)

        # Create test satellite
        self.satellite = Satellite.objects.create(
            sat_name="Test Satellite", sat_number=12345, intl_designator="2024-001A"
        )

        # Create test location
        self.location = Location.objects.create(
            obs_lat_deg=20.0, obs_long_deg=-155.0, obs_alt_m=3000.0
        )

        # Create test observation
        self.observation = Observation.objects.create(
            satellite_id=self.satellite,
            location_id=self.location,
            obs_time_utc=timezone.now(),
            obs_time_uncert_sec=0.1,
            apparent_mag=10.0,
            apparent_mag_uncert=0.1,
            instrument="TEST-SCOPE",
            obs_mode="CCD",
            obs_filter="Clear",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
            sat_ra_deg=100.0,
            sat_dec_deg=20.0,
        )

        # Create a second observation
        self.observation2 = Observation.objects.create(
            satellite_id=self.satellite,
            location_id=self.location,
            obs_time_utc=timezone.now(),
            obs_time_uncert_sec=0.1,
            apparent_mag=4.0,
            apparent_mag_uncert=0.1,
            instrument="TEST-SCOPE",
            obs_mode="CCD",
            obs_filter="Clear",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
            sat_ra_deg=120.0,
            sat_dec_deg=25.0,
        )

    def test_get_observation(self):
        """Test getting a single observation"""
        response = self.client.get(f"/observation/{self.observation.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Test basic fields
        self.assertEqual(data["id"], self.observation.id)
        self.assertEqual(data["satellite_number"], self.satellite.sat_number)
        self.assertEqual(data["satellite_name"], self.satellite.sat_name)

        # Test location fields
        self.assertEqual(data["obs_lat_deg"], self.location.obs_lat_deg)
        self.assertEqual(data["obs_long_deg"], self.location.obs_long_deg)
        self.assertEqual(data["obs_alt_m"], self.location.obs_alt_m)

    def test_get_satellite_observations(self):
        """Test getting all observations for a satellite"""
        response = self.client.get(
            f"/satellite/{self.satellite.sat_number}/observations"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check for paginated response format
        self.assertIn("items", data)
        self.assertIn("count", data)
        self.assertEqual(data["count"], 2)

        # Check observation data in items
        observation_ids = [obs["id"] for obs in data["items"]]
        self.assertIn(self.observation.id, observation_ids)
        self.assertIn(self.observation2.id, observation_ids)

        # Test with invalid satellite
        response = self.client.get("/satellite/-1/observations?offset=1&limit=1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data.get("items", [])), 0)

    def test_search_observations(self):
        """Test searching observations with filters"""
        # In range
        response = self.client.get(
            f"/search?satellite_number={self.satellite.sat_number}&min_magnitude={11.0}&max_magnitude={9.0}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check paginated response format
        self.assertIn("items", data)
        self.assertIn("count", data)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["items"][0]["id"], self.observation.id)

        # Out of range
        response = self.client.get(
            f"/search?satellite_number={self.satellite.sat_number}&min_magnitude={6.0}&max_magnitude={5.0}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(len(data["items"]), 0)

        response = self.client.get(
            f"/search?satellite_number={self.satellite.sat_number}&min_magnitude={9.0}&max_magnitude={11.0}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(len(data["items"]), 0)

    def test_get_satellites(self):
        """Test getting all satellites"""
        response = self.client.get("/satellites")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["sat_number"], self.satellite.sat_number)
        self.assertEqual(data[0]["sat_name"], self.satellite.sat_name)

    def test_get_observations(self):
        """Test getting all observations"""
        response = self.client.get("/observations")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Test paginated response structure
        self.assertIn("items", data)
        # Test count
        self.assertEqual(len(data["items"]), 2)

        # Test that both observations are present
        observation_ids = {obs["id"] for obs in data["items"]}
        self.assertIn(self.observation.id, observation_ids)
        self.assertIn(self.observation2.id, observation_ids)
