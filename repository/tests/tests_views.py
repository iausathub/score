from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from repository.forms import DataChangeForm, GenerateCSVForm, SearchForm
from repository.models import Location, Observation, Satellite
from repository.views import generate_csv


class TestViews(TestCase):
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

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/index.html")
        self.assertContains(response, "STARLINK-123")
        self.assertContains(response, "satellites")
        self.assertContains(response, "observers")

    def test_index_post_no_file(self):
        response = self.client.post(reverse("root"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error"], "Please select a file to upload.")

    def test_data_format(self):
        response = self.client.get("/data-format")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/data-format.html")

    def test_view_data(self):
        response = self.client.get("/view")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/view.html")
        self.assertContains(response, "STARLINK-123")
        self.assertContains(response, "VISUAL")
        self.assertContains(response, "5.2")
        self.assertContains(response, self.obs_date.strftime("%b. %d, %Y"))

    def test_download_all(self):
        response = self.client.get("/download-all")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/zip", response["Content-Type"])
        self.assertTrue(
            response["Content-Disposition"].startswith("attachment; filename=")
        )

    def test_search(self):
        response = self.client.get("/search")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/search.html")

    def test_generate_csv(self):
        response = self.client.get("/generate-csv")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/generate-csv.html")

    def test_satellites_page(self):
        response = self.client.get(reverse("satellites"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/satellites.html")
        self.assertContains(response, self.satellite.sat_name)

    def test_satellite_detail_view(self):
        response = self.client.get(reverse("satellite-data-view", args=[12345]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/satellites/data_view.html")
        self.assertContains(response, self.satellite.sat_name)
        self.assertContains(response, self.satellite.sat_number)

    def test_observer_obs_list_view(self):
        response = self.client.get(
            reverse("observer-view", args=["0123-4567-8910-1112"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/observer_view.html")

        orcid = self.observation.obs_orc_id[0].replace("[", "").replace("]", "")
        self.assertContains(response, orcid)

    def test_last_observer_location_with_observations(self):
        response = self.client.post(
            reverse("last_observer_location"),
            {
                "observer_orcid": "0123-4567-8910-1112",
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "observer_latitude_deg": 33,
            "observer_longitude_deg": -117,
            "observer_altitude_m": 100,
        }

    def test_last_observer_location_invalid_orcid(self):
        response = self.client.post(
            reverse("last_observer_location"),
            {
                "observer_orcid": "0",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"error": "pass"}

    def test_last_observer_location_no_observations(self):
        response = self.client.post(
            reverse("last_observer_location"),
            {
                "observer_orcid": "0123-4567-8910-1113",
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "error": "No observations found for the provided ORCID."
        }


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
def test_generate_csv_get(request_factory):
    request = request_factory.get("/generate_csv/")
    response = generate_csv(request)
    assert response.status_code == 200
    assert "form" in str(response.content)


class SearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.obs_date = timezone.now()
        self.satellite = Satellite.objects.create(
            sat_name="STARLINK-123", sat_number=12345
        )
        self.location = Location.objects.create(
            obs_lat_deg=33,
            obs_long_deg=-117,
            obs_alt_m=100,
            date_added=timezone.now(),
        )

        self.observation = Observation.objects.create(
            satellite_id=self.satellite,
            obs_mode="VISUAL",
            obs_time_utc="2024-01-02T23:59:59.123Z",
            obs_email="abc@def.com",
            location_id=self.location,
            date_added=self.obs_date,
            obs_time_uncert_sec=5,
            apparent_mag=5.2,
            apparent_mag_uncert=0.1,
            obs_filter="CLEAR",
            instrument="none",
            obs_orc_id=["0123-4567-8910-1112"],
        )

    def test_search_get(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], SearchForm)

    def test_search_post_success(self):
        response = self.client.post(
            reverse("search"),
            {
                "sat_name": "STARLINK-123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("STARLINK-123", response.content.decode())

    def test_search_post_no_results(self):
        response = self.client.post(
            reverse("search"),
            {
                "sat_name": "NONEXISTENT",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No observations found")

    def test_search_post_empty(self):
        # Test initial page load with empty search
        response = self.client.post(
            reverse("search"),
            {
                "sat_name": "",
                "sat_number": "",
                "obs_mode": "",
                "start_date_range": "",
                "end_date_range": "",
                "observation_id": "",
                "observer_orcid": "",
                "instrument": "",
            },
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("search"),
            {
                "sat_name": "",
                "sat_number": "",
                "obs_mode": "",
                "start_date_range": "",
                "end_date_range": "",
                "observation_id": "",
                "observer_orcid": "",
                "instrument": "",
                "limit": "25",
                "offset": "0",
                "sort": "date_added",
                "order": "desc",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data["rows"]) > 0)
        self.assertEqual(data["rows"][0]["satellite_name"], "STARLINK-123")
        self.assertIn("obs_ids", data)
        self.assertIsInstance(data["obs_ids"], list)
        self.assertTrue(len(data["obs_ids"]) > 0)

    def test_search_with_date_filter_updates_obs_ids(self):
        """Test search with date filters returns correct obs_ids"""
        # Create observations on different dates
        base_date = timezone.now()
        old_obs = Observation.objects.create(
            satellite_id=self.satellite,
            location_id=self.location,
            obs_time_utc=base_date - timedelta(days=30),
            obs_time_uncert_sec=1.0,
            instrument="Test",
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
        )
        recent_obs = Observation.objects.create(
            satellite_id=self.satellite,
            location_id=self.location,
            obs_time_utc=base_date - timedelta(days=5),
            obs_time_uncert_sec=1.0,
            instrument="Test",
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
        )

        # Search with date filter (last 10 days)
        start_date = (base_date - timedelta(days=10)).date()
        response = self.client.post(
            reverse("search"),
            {
                "sat_name": "",
                "sat_number": "",
                "obs_mode": "",
                "start_date_range": start_date.isoformat(),
                "end_date_range": "",
                "observation_id": "",
                "observer_orcid": "",
                "instrument": "",
                "limit": "25",
                "offset": "0",
                "sort": "date_added",
                "order": "desc",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify obs_ids contains only recent observation, not old one
        self.assertIn("obs_ids", data)
        self.assertIn(recent_obs.id, data["obs_ids"])
        self.assertNotIn(old_obs.id, data["obs_ids"])

    def test_custom_404(self):
        # Test the custom 404 handler
        response = self.client.get("/nonexistent-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_about(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/about.html")

    def test_getting_started(self):
        response = self.client.get(reverse("getting-started"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/getting-started.html")

    def test_download_data(self):
        response = self.client.get(reverse("download-data"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/download-data.html")
        # Check if recaptcha key is in context
        self.assertIn("recaptcha_public_key", response.context)

    def test_policy(self):
        response = self.client.get(reverse("policy"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/policy.html")

    def test_data_change_get(self):
        response = self.client.get(reverse("data-change"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/data-change.html")
        self.assertIsInstance(response.context["form"], DataChangeForm)

    @patch("repository.views.send_data_change_email")
    def test_data_change_post_valid(self, mock_send_email):
        data = {
            "contact_email": "test@example.com",
            "obs_ids": "1,2,3",
            "reason": "Test reason for change",
        }
        response = self.client.post(reverse("data-change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/data-change.html")
        self.assertIn("Your request has been submitted", response.content.decode())
        mock_send_email.assert_called_once_with(
            data["contact_email"], data["obs_ids"], data["reason"]
        )

    def test_data_change_post_invalid(self):
        data = {
            "contact_email": "invalid-email",  # Invalid email format
            "obs_ids": "",  # Required field
            "reason": "",  # Required field
        }
        response = self.client.post(reverse("data-change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/data-change.html")
        self.assertIsInstance(response.context["form"], DataChangeForm)

    def test_download_obs_ids_post(self):
        # Create test data
        obs_ids = [str(self.observation.id)]
        response = self.client.post(
            reverse("download-obs-ids"), {"obs_ids": ",".join(obs_ids)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertTrue(
            response["Content-Disposition"].startswith("attachment; filename=")
        )

    def test_download_obs_ids_get(self):
        response = self.client.get(reverse("download-obs-ids"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "")

    def test_download_results_post(self):
        # Create test data
        obs_ids = [str(self.observation.id)]
        response = self.client.post(
            reverse("download-results"),
            {
                "obs_ids": f"[{', '.join(obs_ids)}]",
                "satellite_name": self.satellite.sat_name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertTrue(
            response["Content-Disposition"].startswith("attachment; filename=")
        )

    def test_download_results_get(self):
        response = self.client.get(reverse("download-results"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "")

    def test_tools(self):
        response = self.client.get(reverse("tools"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/tools.html")

    def test_generate_csv_get(self):
        response = self.client.get(reverse("generate-csv"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/generate-csv.html")
        self.assertIsInstance(response.context["form"], GenerateCSVForm)

    def test_generate_csv_post_valid(self):
        data = {
            "output": "STARLINK-123,12345,2024-03-19T12:00:00Z,0.1,5.0,0.1,33.0,-117.0,100,10,none,VISUAL,CLEAR,test@example.com,0000-0000-0000-0000,185.0,25.0,0,0,0,500,0,0,0,test comment,,",  # noqa: E501
        }
        response = self.client.post(reverse("generate-csv"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertTrue(
            response["Content-Disposition"].startswith("attachment; filename=")
        )

    @patch("repository.views.get_satellite_name")
    def test_name_id_lookup_with_norad_id(self, mock_get_name):
        mock_get_name.return_value = "STARLINK-123"
        response = self.client.post(
            reverse("name-id-lookup"),
            {
                "satellite_id": "12345",
                "satellite_name": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["satellite_name"], "STARLINK-123")
        self.assertEqual(data["norad_id"], "12345")

    @patch("repository.views.get_norad_id")
    def test_name_id_lookup_with_name(self, mock_get_id):
        mock_get_id.return_value = "12345"
        response = self.client.post(
            reverse("name-id-lookup"),
            {
                "satellite_name": "STARLINK-123",
                "satellite_id": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["satellite_name"], "STARLINK-123")
        self.assertEqual(data["norad_id"], "12345")

    def test_name_id_lookup_with_both(self):
        response = self.client.post(
            reverse("name-id-lookup"),
            {
                "satellite_id": "12345",
                "satellite_name": "STARLINK-123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"error": "Please provide either a NORAD ID or a satellite name."},
        )

    @patch("repository.views.requests.get")
    def test_satellite_pos_lookup_with_norad_id(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "fields": [
                "name",
                "catalog_id",
                "altitude_deg",
                "azimuth_deg",
                "right_ascension_deg",
                "declination_deg",
                "tle_date",
            ],
            "data": [["STARLINK-123", "12345", 45.0, 180.0, 100.0, 20.0, "2024-03-19"]],
        }

        response = self.client.post(
            reverse("satellite-pos-lookup"),
            {
                "satellite_id": "12345",
                "satellite_name": "",
                "obs_lat": "33.0",
                "obs_long": "-117.0",
                "obs_alt": "100",
                "day": "19",
                "month": "3",
                "year": "2024",
                "hour": "12",
                "minutes": "0",
                "seconds": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["satellite_name"], "STARLINK-123")
        self.assertEqual(data["norad_id"], "12345")
        self.assertEqual(data["altitude"], 45.0)
        self.assertEqual(data["azimuth"], 180.0)
        self.assertEqual(data["ra"], 100.0)
        self.assertEqual(data["dec"], 20.0)
        self.assertEqual(data["tle_date"], "2024-03-19")

    def test_satellite_pos_lookup_missing_fields(self):
        response = self.client.post(
            reverse("satellite-pos-lookup"),
            {
                "satellite_id": "12345",
                # Missing required fields
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"error": "One or more required fields are empty."}
        )

    def test_satellite_pos_lookup_with_both_id_and_name(self):
        response = self.client.post(
            reverse("satellite-pos-lookup"),
            {
                "satellite_id": "12345",
                "satellite_name": "STARLINK-123",
                "obs_lat": "33.0",
                "obs_long": "-117.0",
                "obs_alt": "100",
                "day": "19",
                "month": "3",
                "year": "2024",
                "hour": "12",
                "minutes": "0",
                "seconds": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"error": "Please provide either a NORAD ID or a satellite name."},
        )

    def test_satellite_observations_not_found(self):
        response = self.client.get(reverse("satellite-observations", args=[99999]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Satellite not found"})

    def test_satellite_observations_found(self):
        response = self.client.get(
            reverse("satellite-observations", args=[self.satellite.sat_number])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["rows"]), 1)  # One observation from setUp
        obs_data = data["rows"][0]
        self.assertEqual(obs_data["obs_mode"], self.observation.obs_mode)
        self.assertEqual(obs_data["apparent_mag"], self.observation.apparent_mag)

    def test_satellite_observations_sorting(self):
        # Create a second observation for testing sorting
        second_obs = Observation.objects.create(  # noqa: F841
            obs_time_utc=self.obs_date + timezone.timedelta(days=1),
            obs_email="abc@def.com",
            satellite_id=self.satellite,
            location_id=self.location,
            date_added=self.obs_date + timezone.timedelta(days=1),
            obs_time_uncert_sec=5,
            apparent_mag=4.2,  # Different magnitude for sorting test
            apparent_mag_uncert=0.1,
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            instrument="none",
            obs_orc_id=["0123-4567-8910-1112"],
        )

        # Test sorting by date added ascending
        response = self.client.get(
            reverse("satellite-observations", args=[self.satellite.sat_number])
            + "?sort=added&order=asc"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["rows"]), 2)
        # Compare timestamps instead of formatted dates
        self.assertLess(data["rows"][0]["added"], data["rows"][1]["added"])

        # Test sorting by magnitude descending
        response = self.client.get(
            reverse("satellite-observations", args=[self.satellite.sat_number])
            + "?sort=apparent_mag&order=desc"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["rows"]), 2)
        self.assertGreater(
            float(data["rows"][0]["apparent_mag"]),
            float(data["rows"][1]["apparent_mag"]),
        )

    def test_satellite_observations_pagination(self):
        # Create additional observations for pagination testing
        for i in range(
            7
        ):  # This will create 8 observations total (including the one from setUp)
            Observation.objects.create(
                obs_time_utc=self.obs_date + timezone.timedelta(days=i),
                obs_email="abc@def.com",
                satellite_id=self.satellite,
                location_id=self.location,
                date_added=self.obs_date + timezone.timedelta(days=i),
                obs_time_uncert_sec=5,
                apparent_mag=5.0 + i * 0.1,
                apparent_mag_uncert=0.1,
                obs_mode="VISUAL",
                obs_filter="CLEAR",
                instrument="none",
                obs_orc_id=["0123-4567-8910-1112"],
            )

        # Test default pagination (limit=5)
        response = self.client.get(
            reverse("satellite-observations", args=[self.satellite.sat_number])
        )
        data = response.json()
        self.assertEqual(len(data["rows"]), 5)  # Default limit
        self.assertEqual(data["total"], 8)  # Total observations
        self.assertEqual(data["debug"]["limit"], 5)
        self.assertEqual(data["debug"]["offset"], 0)

        # Test custom limit and offset
        response = self.client.get(
            reverse("satellite-observations", args=[self.satellite.sat_number])
            + "?limit=3&offset=3"
        )
        data = response.json()
        self.assertEqual(len(data["rows"]), 3)
        self.assertEqual(data["debug"]["limit"], 3)
        self.assertEqual(data["debug"]["offset"], 3)
        self.assertEqual(data["debug"]["page"], 2)

    def test_get_observation_by_id_found(self):
        response = self.client.get(
            reverse("get_observation_by_id", args=[self.observation.id])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.observation.id)
        self.assertEqual(data["obs_mode"], self.observation.obs_mode)
        self.assertEqual(data["obs_filter"], self.observation.obs_filter)
        self.assertEqual(data["apparent_mag"], self.observation.apparent_mag)

    def test_get_observation_by_id_not_found(self):
        response = self.client.get(reverse("get_observation_by_id", args=[99999]))
        self.assertEqual(response.status_code, 404)


class LaunchViewTests(TestCase):
    def setUp(self):
        # Create test location once for all tests
        self.location = Location.objects.create(
            obs_lat_deg=33,
            obs_long_deg=-117,
            obs_alt_m=100,
            date_added=timezone.now(),
        )

        # Create base test satellites
        self.satellite1 = Satellite.objects.create(
            sat_name="Test-1", sat_number="12345", intl_designator="2023-001A"
        )
        self.satellite2 = Satellite.objects.create(
            sat_name="Test-2", sat_number="12346", intl_designator="2023-001B"
        )
        self.satellite3 = Satellite.objects.create(
            sat_name="Different-Launch", sat_number="12347", intl_designator="2023-002A"
        )
        self.satellite_no_designator = Satellite.objects.create(
            sat_name="No-Designator", sat_number="12348"
        )

    def create_observation(self, satellite):
        """Helper method to create an observation"""
        return Observation.objects.create(
            satellite_id=satellite,
            obs_time_utc=timezone.now(),
            obs_time_uncert_sec=1.0,
            instrument="none",
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
            location_id=self.location,
        )

    def test_launch_view_basic(self):
        """Test basic launch view functionality"""
        response = self.client.get(reverse("launch-view", args=["2023-001"]))
        self.assertEqual(response.status_code, 200)
        satellites = response.context["satellites"]

        # Check correct satellites are included/excluded
        self.assertEqual(len(satellites), 2)
        self.assertIn(self.satellite1, satellites)
        self.assertIn(self.satellite2, satellites)
        self.assertNotIn(self.satellite3, satellites)
        self.assertNotIn(self.satellite_no_designator, satellites)

    def test_launch_number_extraction(self):
        """Test launch number extraction from international designators"""
        test_cases = [
            ("2023-001A", "2023-001"),  # Standard format
            ("2023-001AA", "2023-001"),  # Multiple letters
            ("", None),  # Empty string
            (None, None),  # No designator
        ]

        for designator, expected in test_cases:
            if expected:  # Only test valid designators
                response = self.client.get(reverse("launch-view", args=[expected]))
                self.assertEqual(response.status_code, 200)
                if designator:
                    satellites = response.context["satellites"]
                    matching_sats = [
                        s for s in satellites if s.intl_designator.startswith(expected)
                    ]
                    self.assertTrue(len(matching_sats) > 0)

    def test_observation_counting(self):
        """Test observation counting for satellites in same launch"""
        # Create observations
        self.create_observation(self.satellite1)
        self.create_observation(self.satellite1)
        self.create_observation(self.satellite2)

        response = self.client.get(reverse("launch-view", args=["2023-001"]))
        satellites = response.context["satellites"]

        # Check observation counts
        counts = {s.sat_number: s.num_observations for s in satellites}
        self.assertEqual(counts[self.satellite1.sat_number], 2)
        self.assertEqual(counts[self.satellite2.sat_number], 1)


class VisualizationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.obs_date = timezone.now()
        self.location = Location.objects.create(
            obs_lat_deg=33,
            obs_long_deg=-117,
            obs_alt_m=100,
            date_added=timezone.now(),
        )
        # Create satellites from different constellations
        self.starlink_sat = Satellite.objects.create(
            sat_name="STARLINK-12345", sat_number=50001
        )
        self.oneweb_sat = Satellite.objects.create(
            sat_name="ONEWEB-0001", sat_number=50002
        )
        self.other_sat = Satellite.objects.create(
            sat_name="RANDOM-SAT", sat_number=50003
        )

        # Create observations with satchecker data for visualization
        self.starlink_obs = Observation.objects.create(
            satellite_id=self.starlink_sat,
            obs_time_utc=self.obs_date,
            obs_time_uncert_sec=1.0,
            apparent_mag=5.5,
            apparent_mag_uncert=0.1,
            instrument="none",
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
            location_id=self.location,
            alt_deg_satchecker=45.0,
            az_deg_satchecker=180.0,
            sat_altitude_km_satchecker=550.0,
            solar_elevation_deg_satchecker=-15.0,
        )
        self.oneweb_obs = Observation.objects.create(
            satellite_id=self.oneweb_sat,
            obs_time_utc=self.obs_date,
            obs_time_uncert_sec=1.0,
            apparent_mag=6.0,
            apparent_mag_uncert=0.1,
            instrument="none",
            obs_mode="VISUAL",
            obs_filter="CLEAR",
            obs_email="test@example.com",
            obs_orc_id=["0000-0000-0000-0000"],
            location_id=self.location,
            alt_deg_satchecker=30.0,
            az_deg_satchecker=90.0,
            sat_altitude_km_satchecker=600.0,
            solar_elevation_deg_satchecker=-20.0,
        )

    def test_visualization_view_basic(self):
        response = self.client.get(reverse("data-visualization"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/data_visualization.html")

    def test_visualization_view_context_data(self):
        response = self.client.get(reverse("data-visualization"))
        self.assertEqual(response.status_code, 200)

        # Check that constellation stats are present
        self.assertIn("constellation_stats", response.context)
        self.assertIn("magnitude_bins", response.context)
        self.assertIn("observations", response.context)

        # Check that at least starlink and oneweb appear in the stats
        constellation_stats = response.context["constellation_stats"]
        constellation_names = [stat["name"] for stat in constellation_stats]
        self.assertIn("Starlink", constellation_names)
        self.assertIn("OneWeb", constellation_names)

    def test_visualization_view_observations_data(self):
        response = self.client.get(reverse("data-visualization"))
        observations = response.context["observations"]

        # Should have at least our 2 test observations
        self.assertGreaterEqual(len(observations), 2)

        # Check observation data structure
        for obs in observations:
            self.assertIn("alt_deg_satchecker", obs)
            self.assertIn("az_deg_satchecker", obs)
            self.assertIn("magnitude", obs)

    def test_graphs_view(self):
        response = self.client.get(reverse("graphs"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/visualization/graphs.html")

    def test_plots_view(self):
        response = self.client.get(reverse("plots"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/visualization/plots.html")

    def test_get_satellite_data_endpoint(self):
        response = self.client.get(reverse("satellite-data"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("constellations", data)

        # Check that starlink constellation exists in the response
        constellations = data["constellations"]
        self.assertIn("starlink", constellations)
        self.assertGreater(constellations["starlink"]["count"], 0)

    def test_get_observations_for_satellites_no_filters(self):
        response = self.client.get(reverse("observations-for-satellites"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("observations", data)
        self.assertIn("count", data)

    def test_get_observations_for_satellites_with_constellation_filter(self):
        response = self.client.get(
            reverse("observations-for-satellites"), {"constellations[]": ["starlink"]}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        observations = data["observations"]

        # All observations should be from Starlink
        for obs in observations:
            self.assertEqual(obs["constellation"], "starlink")

    def test_get_observations_for_satellites_with_magnitude_filter(self):
        response = self.client.get(
            reverse("observations-for-satellites"), {"min_mag": "5.0", "max_mag": "5.6"}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        observations = data["observations"]

        # All observations should be within magnitude range
        for obs in observations:
            self.assertGreaterEqual(obs["magnitude"], 5.0)
            self.assertLessEqual(obs["magnitude"], 5.6)

    def test_get_observations_for_satellites_with_satellite_elevation_filter(self):
        response = self.client.get(
            reverse("observations-for-satellites"),
            {"min_sat_elev": "540", "max_sat_elev": "560"},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        observations = data["observations"]

        # All observations should be within satellite elevation range
        for obs in observations:
            if obs["sat_altitude_km_satchecker"] is not None:
                self.assertGreaterEqual(obs["sat_altitude_km_satchecker"], 540)
                self.assertLessEqual(obs["sat_altitude_km_satchecker"], 560)

    def test_get_observations_for_satellites_with_solar_elevation_filter(self):
        response = self.client.get(
            reverse("observations-for-satellites"),
            {"min_solar_elev": "-20", "max_solar_elev": "-10"},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        observations = data["observations"]

        # All observations should be within solar elevation range
        for obs in observations:
            if obs["solar_elevation_deg_satchecker"] is not None:
                self.assertGreaterEqual(obs["solar_elevation_deg_satchecker"], -20)
                self.assertLessEqual(obs["solar_elevation_deg_satchecker"], -10)

    def test_get_observations_for_satellites_with_date_filter(self):
        start_date = (self.obs_date - timezone.timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (self.obs_date + timezone.timedelta(days=1)).strftime("%Y-%m-%d")

        response = self.client.get(
            reverse("observations-for-satellites"),
            {"start_date": start_date, "end_date": end_date},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["count"], 0)
