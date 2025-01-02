import pytest
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from repository.forms import SearchForm
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
