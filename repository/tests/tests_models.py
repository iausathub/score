from django.db import transaction
from django.forms import ValidationError
from django.test import TestCase
from django.utils import timezone

from repository.models import Location, Observation, Satellite


class SatelliteTest(TestCase):
    def create_satellite(self, sat_name="STARLINK-123", sat_number=12345):
        return Satellite.objects.create(
            sat_name=sat_name,
            sat_number=sat_number,
            date_added=timezone.now(),
        )

    def test_satellite_creation(self):
        sat = self.create_satellite()
        self.assertTrue(isinstance(sat, Satellite))
        self.assertEqual(sat.__str__(), str(sat.sat_number) + ", " + sat.sat_name)

    def test_satellite_validation(self):
        # field is required
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number="")

        # field is required
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number=None)

        # field must be in valid range
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number=1234567)

        # field must be in valid range
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number=-12345)

        # field must be valid format
        with self.assertRaises(ValueError):
            sat = self.create_satellite(sat_number="test")

        # valid values successful
        sat = self.create_satellite()  # noqa: F841


class LocationTest(TestCase):
    def create_location(self, obs_lat_deg=33, obs_long_deg=-117, obs_alt_m=100):
        return Location.objects.create(
            obs_lat_deg=obs_lat_deg,
            obs_long_deg=obs_long_deg,
            obs_alt_m=obs_alt_m,
            date_added=timezone.now(),
        )

    def test_location_creation(self):
        loc = self.create_location()
        self.assertTrue(isinstance(loc, Location))
        self.assertEqual(
            loc.__str__(),
            str(loc.obs_lat_deg)
            + ", "
            + str(loc.obs_long_deg)
            + ", "
            + str(loc.obs_alt_m),
        )

    def test_location_validation(self):
        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                loc = self.create_location(obs_lat_deg="")

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                loc = self.create_location(obs_lat_deg=None)

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                loc = self.create_location(obs_long_deg="")

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                loc = self.create_location(obs_long_deg=None)

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                loc = self.create_location(obs_alt_m="")

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                loc = self.create_location(obs_alt_m=None)

        # field must be in valid range
        with self.assertRaises(ValidationError):
            loc = self.create_location(obs_lat_deg=-91)
            loc.full_clean()

        # field must be in valid range
        with self.assertRaises(ValidationError):
            loc = self.create_location(obs_lat_deg=91)
            loc.full_clean()

        # field must be in valid range
        with self.assertRaises(ValidationError):
            loc = self.create_location(obs_long_deg=-181)
            loc.full_clean()

        # field must be in valid range
        with self.assertRaises(ValidationError):
            loc = self.create_location(obs_long_deg=181)
            loc.full_clean()

        # valid values successful
        loc = self.create_location()


class ObservationTest(TestCase):
    timestamp = timezone.now()
    orc_id = ["0000-1234-5678-9101"]

    def create_observation(
        self,
        obs_email="test@abc.com",
        obs_time_utc=timestamp,
        obs_lat_deg=33,
        obs_long_deg=-117,
        obs_alt_m=100,
        obs_time_uncert_sec=0.0,
        apparent_mag=0.0,
        apparent_mag_uncert=0.0,
        obs_mode="VISUAL",
        obs_filter="test",
        instrument="test",
        obs_orc_id=orc_id,
        sat_number=12345,
    ):
        sat = Satellite.objects.create(
            sat_name="STARLINK-123",
            sat_number=sat_number,
            date_added=timezone.now(),
        )
        loc = Location.objects.create(
            obs_lat_deg=obs_lat_deg,
            obs_long_deg=obs_long_deg,
            obs_alt_m=obs_alt_m,
            date_added=timezone.now(),
        )

        return Observation.objects.create(
            obs_time_utc=obs_time_utc,
            obs_email=obs_email,
            satellite_id=sat,
            location_id=loc,
            date_added=timezone.now(),
            obs_time_uncert_sec=obs_time_uncert_sec,
            apparent_mag=apparent_mag,
            apparent_mag_uncert=apparent_mag_uncert,
            obs_mode=obs_mode,
            obs_filter=obs_filter,
            instrument=instrument,
            obs_orc_id=obs_orc_id,
        )

    def test_observation_creation(self):
        obs = self.create_observation()
        self.assertTrue(isinstance(obs, Observation))
        self.assertEqual(
            obs.__str__(),
            str(obs.id)
            + ", "
            + obs.satellite_id.sat_name
            + ", "
            + str(obs.obs_time_utc)
            + ", "
            + obs.obs_email,
        )

    def test_observation_creation_bad_satellite(self):
        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(sat_number=1234567)  # noqa: F841
            self.assertIn("NORAD ID must be 6 digits or less.", str(error.exception))

    def test_observation_validation(self):
        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_time_utc=None, sat_number=123)
            self.assertIn("This field cannot be null", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_time_utc="", sat_number=1)
            self.assertIn("value has an invalid format", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_time_uncert_sec=None, sat_number=2)
            self.assertIn("This field cannot be null", str(error.exception))

        # field must be positive
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_time_uncert_sec=-1, sat_number=3)
            obs.full_clean()
        self.assertIn(
            "Ensure this value is greater than or equal to 0.", str(error.exception)
        )

        # field is required
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_email="", sat_number=4)
            print(error.exception)
            obs.full_clean()
        self.assertIn("This field cannot be blank.", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_email=None, sat_number=5)
                print(error.exception)
            self.assertIn("This field cannot be null", str(error.exception))

        # field must be valid email
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_email="test", sat_number=6)
            obs.full_clean()
        self.assertIn("Enter a valid email address", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(
                    apparent_mag=3, apparent_mag_uncert=None, sat_number=7
                )
            self.assertIn(
                "Apparent magnitude uncertainty is required if apparent magnitude is provided.",  # noqa: E501
                str(error.exception),
            )

        # field must be positive
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(apparent_mag_uncert=-1, sat_number=8)
            obs.full_clean()
        self.assertIn(
            "Ensure this value is greater than or equal to 0.", str(error.exception)
        )

        # field is required
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_mode="", sat_number=9)
            obs.full_clean()
        self.assertIn("This field cannot be blank", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_mode=None, sat_number=10)
            self.assertIn("This field cannot be null", str(error.exception))

        # field is required
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_mode="test", sat_number=11)
            obs.full_clean()
        self.assertIn(
            "Observation mode must be one of the following", str(error.exception)
        )

        # field is required
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_filter="", sat_number=12)
            obs.full_clean()
        self.assertIn("This field cannot be blank", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_filter=None, sat_number=13)
            self.assertIn("This field cannot be null", str(error.exception))

        # field is required
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(instrument="", sat_number=14)
            obs.full_clean()
        self.assertIn("This field cannot be blank", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(instrument=None, sat_number=15)
            self.assertIn("This field cannot be null", str(error.exception))

        # field is required
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_orc_id=[""], sat_number=16)
            obs.full_clean()
        self.assertIn("ORCID cannot be empty", str(error.exception))

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError) as error:
                obs = self.create_observation(obs_orc_id=None, sat_number=17)
            self.assertIn("This field cannot be null.", str(error.exception))

        # field must be valid ORCID
        with self.assertRaises(TypeError) as error:
            obs = self.create_observation(obs_orc_id=1, sat_number=18)
            obs.full_clean()
        self.assertIn("is not iterable", str(error.exception))

        # field must be valid ORCID
        with self.assertRaises(ValidationError) as error:
            obs = self.create_observation(obs_orc_id=["n/a"], sat_number=19)
            obs.full_clean()
        self.assertIn("not a valid ORCID", str(error.exception))

        # valid values successful
        obs = self.create_observation()
        obs.full_clean()
