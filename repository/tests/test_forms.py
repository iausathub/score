from unittest.mock import patch

from django.test import Client, TestCase

from repository.forms import GenerateCSVForm


class GenerateCSVFormTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_form_valid_required(self):
        form = GenerateCSVForm(
            {
                "sat_number": 12345,
                "obs_date_year": 2024,
                "obs_date_month": 1,
                "obs_date_day": 2,
                "obs_date_hour": 23,
                "obs_date_min": 59,
                "obs_date_sec": 59,
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
                "limiting_magnitude": 10,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": -117,
                "observer_altitude_m": 100,
                "obs_mode": "VISUAL",
                "filter": "CLEAR",
                "instrument": "n/a",
                "observer_email": "abc@123.com",
                "observer_orcid": "0123-4567-8910-1112",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_valid_optional(self):
        form = GenerateCSVForm(
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "obs_date_year": 2024,
                "obs_date_month": 1,
                "obs_date_day": 2,
                "obs_date_hour": 23,
                "obs_date_min": 59,
                "obs_date_sec": 59,
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
                "limiting_magnitude": 10,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": -117,
                "observer_altitude_m": 100,
                "obs_mode": "VISUAL",
                "filter": "CLEAR",
                "instrument": "n/a",
                "observer_email": "abc@123.com",
                "observer_orcid": "0123-4567-8910-1112",
                "sat_ra_deg": 359.1234,
                "sat_dec_deg": -40.1234,
                "sigma_2_ra": 0.03,
                "sigma_2_dec": 0.03,
                "sigma_ra_sigma_dec": 0.01,
                "range_to_sat_km": 560.123,
                "range_to_sat_uncert_km": 5,
                "range_rate_sat_km_s": 3.123,
                "range_rate_sat_uncert_km_s": 0.01,
                "comments": "test comment",
                "data_archive_link": "http://www.test.com",
            }
        )

        self.assertTrue(form.is_valid())

    def test_form_validators(self):

        form = GenerateCSVForm(
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "obs_date_year": 2024,
                "obs_date_month": 1,
                "obs_date_day": 2,
                "obs_date_hour": 23,
                "obs_date_min": 59,
                "obs_date_sec": 59,
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
                "limiting_magnitude": 10,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": 100,
                "observer_altitude_m": 100,
                "obs_mode": "VISUAL",
                "filter": "CLEAR",
                "instrument": "n/a",
                "observer_email": "abc@123",
                "observer_orcid": "0",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "observer_orcid": ["Invalid ORCID."],
                "observer_email": ["Observer email is not correctly formatted."],
            },
        )

    @patch("requests.get")
    def test_invalid_fields(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        response = self.client.post(
            "/generate-csv",
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "obs_date_year": 2024,
                "obs_date_month": 1,
                "obs_date_day": 2,
                "obs_date_hour": 23,
                "obs_date_min": 59,
                "obs_date_sec": 59,
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": "",
                "limiting_magnitude": 10,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": -117,
                "observer_altitude_m": 0,
                "obs_mode": "VISUAL",
                "filter": "",
                "instrument": "",
                "observer_email": "abc",
                "observer_orcid": "0123-4567-8910-1112",
            },
        )

        self.assertEqual(response.status_code, 200)
        form_in_response = response.context["form"]
        self.assertEqual(
            form_in_response.errors,
            {
                "observer_email": ["Observer email is not correctly formatted."],
            },
        )

    def test_abs_mag_uncert(self):

        response = self.client.post(  # noqa: F841
            "/generate-csv",
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "obs_date_year": 2024,
                "obs_date_month": 1,
                "obs_date_day": 2,
                "obs_date_hour": 23,
                "obs_date_min": 59,
                "obs_date_sec": 59,
                "obs_date_uncert": 0.01,
                "apparent_mag_uncert": 0.01,
                "non_detection": "false",
                "limiting_magnitude": 10,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": -117,
                "observer_altitude_m": 100,
                "obs_mode": "VISUAL",
                "filter": "CLEAR",
                "instrument": "n/a",
                "observer_email": "abc@123.com",
                "observer_orcid": "0123-4567-8910-1112",
                "not_detected": "false",
            },
        )
        self.assertFalse(response.context["form"].is_valid())
