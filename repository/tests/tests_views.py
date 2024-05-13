from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from repository.forms import SearchForm
from repository.models import Location, Observation, Satellite


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
        self.assertIs(response.context["form"], SearchForm)

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
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("STARLINK-123", response.content.decode())
