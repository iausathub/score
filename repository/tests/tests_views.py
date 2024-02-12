from django.test import TestCase
from django.utils import timezone

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
            constellation="starlink",
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
            obs_orc_id="0123-4567-8910-1112",
        )

    def test_index(self):
        # need to add test data to test this
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/index.html")
        self.assertContains(response, "STARLINK-123")
        self.assertContains(response, "satellites")
        self.assertContains(response, "observers")

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
        self.assertContains(response, self.obs_date.strftime("%b. %e, %Y"))

    def test_download_all(self):
        response = self.client.get("/download-all")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/zip", response["Content-Type"])

    def test_search(self):
        response = self.client.get("/search")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "repository/search.html")
