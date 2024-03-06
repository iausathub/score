from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils import validate_position


class UtilsTest(TestCase):
    obs_date = timezone.now()

    def setUp(self):
        # Add test data
        self.location = Location.objects.create(
            obs_lat_deg=33,
            obs_long_deg=-117,
            obs_alt_m=100,
            date_added=timezone.now(),
        )
        self.satellite = Satellite.objects.create(
            sat_name="STARLINK-123",
            sat_number=12345,
            date_added=timezone.now(),
        )
        self.observation = Observation.objects.create(
            obs_time_utc=self.obs_date,
            obs_email="abc@def.com",
            satellite_id=self.satellite,
            location_id=self.location,
            date_added=self.obs_date,
            obs_time_uncert_sec=5,
            apparent_mag=5.2,
            apparent_mag_uncert=0.1,
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            instrument="none",
            obs_orc_id=["0123-4567-8910-1112"],
        )

    @patch("requests.get")
    def test_validate_position(self, mock_get):
        # Mock the response from the API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"NAME": "TestSat", "ALTITUDE-DEG": "10"}
        ]

        result = validate_position(
            "TestSat", "12345", "2022-01-01T00:00:00", "0", "0", "0"
        )
        self.assertTrue(result)

    # Test for invalid satellite name
    @patch("requests.get")
    def test_validate_position_invalid_sat_name(self, mock_get):
        # Mock the response from the API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"NAME": "TestSat", "ALTITUDE-DEG": "10"}
        ]

        result = validate_position(
            "InvalidSat", "12345", "2022-01-01T00:00:00", "0", "0", "0"
        )
        self.assertEqual(result, "Satellite name and number do not match")

    # Test for satellite not visible at the time and location
    @patch("requests.get")
    def test_validate_position_not_visible(self, mock_get):
        # Mock the response from the API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []

        result = validate_position(
            "TestSat", "12345", "2022-01-01T00:00:00", "0", "0", "0"
        )
        self.assertEqual(result, "Satellite not visible at this time and location")
