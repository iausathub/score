from django.db import transaction
from django.forms import ValidationError
from django.test import TestCase
from django.utils import timezone

from repository.models import Location, Observation, Satellite


class SatelliteTest(TestCase):
    def create_satellite(
        self, sat_name="STARLINK-123", sat_number=12345, constellation="starlink"
    ):
        return Satellite.objects.create(
            sat_name=sat_name,
            sat_number=sat_number,
            constellation=constellation,
            date_added=timezone.now(),
        )

    def test_satellite_creation(self):
        sat = self.create_satellite()
        self.assertTrue(isinstance(sat, Satellite))
        self.assertEqual(sat.__str__(), sat.sat_name)

    def test_satellite_validation(self):
        # field is required
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_name="")

        # field is required
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_name=None)

        # field is required
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number="")

        # field is required
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number=None)

        # field must be in valid range
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number=123456)

        # field must be in valid range
        with self.assertRaises(ValidationError):
            sat = self.create_satellite(sat_number=-12345)

        # field must be valid format
        with self.assertRaises(ValidationError):
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

        # field must be positive
        with self.assertRaises(ValidationError):
            loc = self.create_location(obs_alt_m=-1)
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
    ):
        sat = Satellite.objects.create(
            sat_name="STARLINK-123",
            sat_number=12345,
            constellation="starlink",
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

    def test_observation_validation(self):
        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_time_utc=None)

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_time_utc="")

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_time_uncert_sec=None)

        # field must be positive
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_time_uncert_sec=-1)
            obs.full_clean()

        # field is required
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_email="")
            obs.full_clean()

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_email=None)

        # field must be valid email
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_email="test")
            obs.full_clean()

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(apparent_mag=3, apparent_mag_uncert=None)

        # field must be positive
        with self.assertRaises(ValidationError):
            obs = self.create_observation(apparent_mag_uncert=-1)
            obs.full_clean()

        # field is required
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_mode="")
            obs.full_clean()

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_mode=None)

        # field is required
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_mode="test")
            obs.full_clean()

        # field is required
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_filter="")
            obs.full_clean()

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_filter=None)

        # field is required
        with self.assertRaises(ValidationError):
            obs = self.create_observation(instrument="")
            obs.full_clean()

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(instrument=None)

        # field is required
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_orc_id=[""])
            obs.full_clean()

        # field is required
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                obs = self.create_observation(obs_orc_id=None)

        # field must be valid ORCID
        with self.assertRaises(TypeError):
            obs = self.create_observation(obs_orc_id=1)
            obs.full_clean()

        # field must be valid ORCID
        with self.assertRaises(ValidationError):
            obs = self.create_observation(obs_orc_id=["n/a"])
            obs.full_clean()

        # valid values successful
        obs = self.create_observation()
        obs.full_clean()
