from django.forms import ValidationError
from django.test import Client, TestCase

from repository.forms import SingleObservationForm


class SingleObservationFormTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_form_required_fields(self):
        form = SingleObservationForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "sat_name": ["This field is required."],
                "sat_number": ["This field is required."],
                "constellation": ["This field is required."],
                "obs_date": ["This field is required."],
                "obs_date_uncert": ["This field is required."],
                "instrument": ["This field is required."],
                "observer_latitude_deg": ["This field is required."],
                "observer_longitude_deg": ["This field is required."],
                "observer_altitude_m": ["This field is required."],
                "obs_mode": ["This field is required."],
                "filter": ["This field is required."],
                "observer_email": ["This field is required."],
                "observer_orcid": ["This field is required."],
            },
        )

    def test_form_valid_required(self):
        form = SingleObservationForm(
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "constellation": "STARLINK",
                "obs_date": "2024-01-02T23:59:59.123Z",
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
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
        form = SingleObservationForm(
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "constellation": "STARLINK",
                "obs_date": "2024-01-02T23:59:59.123Z",
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": -117,
                "observer_altitude_m": 100,
                "obs_mode": "VISUAL",
                "filter": "CLEAR",
                "instrument": "n/a",
                "observer_email": "abc@123.com",
                "observer_orcid": "0123-4567-8910-1112",
                "sat_ra_deg": 359.1234,
                "sat_ra_uncert_deg": 0.01,
                "sat_dec_deg": -40.1234,
                "sat_dec_uncert_deg": 0.03,
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
        form = SingleObservationForm(
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "constellation": "STARLINK",
                "obs_date": "2024-01-02",
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
                "observer_latitude_deg": 33,
                "observer_longitude_deg": 100,
                "observer_altitude_m": 100,
                "obs_mode": "VISUAL",
                "filter": "CLEAR",
                "instrument": "n/a",
                "observer_email": "abc@123.com",
                "observer_orcid": "0123-4567-8910-1112",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "obs_date": ["Invalid date format."],
            },
        )

        form = SingleObservationForm(
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "constellation": "STARLINK",
                "obs_date": "2024-01-02T23:59:59.123Z",
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": 0.01,
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

    def test_invalid_fields(self):
        response = self.client.post(
            "/upload",
            {
                "sat_name": "STARLINK-123",
                "sat_number": 12345,
                "constellation": "STARLINK",
                "obs_date": "2024-01-02T23:59:59.123Z",
                "obs_date_uncert": 0.01,
                "apparent_mag": 8.1,
                "apparent_mag_uncert": "",
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
                "instrument": ["This field is required."],
                "filter": ["This field is required."],
            },
        )

    def test_abs_mag_uncert(self):
        with self.assertRaises(ValidationError):
            response = self.client.post(  # noqa: F841
                "/upload",
                {
                    "sat_name": "STARLINK-123",
                    "sat_number": 12345,
                    "constellation": "STARLINK",
                    "obs_date": "2024-01-02T23:59:59.123Z",
                    "obs_date_uncert": 0.01,
                    "apparent_mag_uncert": 0.01,
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
