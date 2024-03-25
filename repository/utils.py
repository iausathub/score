import csv
import io
import zipfile
from collections import namedtuple

import requests
from astropy.time import Time
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from rest_framework.renderers import JSONRenderer

from repository.models import Observation, Satellite
from repository.serializers import ObservationSerializer


# Statistics for main page
def get_stats():
    stats = namedtuple(
        "stats",
        [
            "satellite_count",
            "observation_count",
            "observer_count",
            "latest_obs_list",
        ],
    )

    observation_count = Observation.objects.count()
    if observation_count == 0:
        return stats(0, 0, 0, [])
    satellite_count = Satellite.objects.count()

    observer_count = (
        Observation.objects.values("location_id", "obs_email").distinct().count()
    )
    latest_obs_list = Observation.objects.order_by("-date_added")[:7]

    # JSON is also needed for the modal view when an observation in the list is clicked
    observation_list_json = [
        (JSONRenderer().render(ObservationSerializer(observation).data))
        for observation in latest_obs_list
    ]
    observations_and_json = zip(latest_obs_list, observation_list_json)

    return stats(
        satellite_count, observation_count, observer_count, observations_and_json
    )


# Validate satellite position is above horizon using SatChecker
def validate_position(
    satellite_name, sat_number, observation_time, latitude, longitude, altitude
):
    if (
        not satellite_name
        or not sat_number
        or not observation_time
        or not latitude
        or not longitude
        or not altitude
    ):
        return False
    obs_time = Time(observation_time, format="isot", scale="utc")
    url = "https://cps.iau.org/tools/satchecker/api/ephemeris/catalog-number/"
    params = {
        "catalog": sat_number,
        "latitude": latitude,
        "longitude": longitude,
        "elevation": altitude,
        "julian_date": obs_time.jd,
        "min_altitude": -5,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException:
        return "Satellite position check failed - try again later."

    if r.status_code != 200:
        return "Satellite position check failed - verify uploaded data is correct."
    if not r.json():
        return "Satellite with this ID not visible at this time and location"
    if r.json()[0]["NAME"] != satellite_name:
        return "Satellite name and number do not match"
    if float(r.json()[0]["ALTITUDE-DEG"]) < -5:
        return "Satellite below horizon"
    return True


# Send upload confirmation with observation IDs for reference
def send_confirmation_email(obs_ids, email_address):
    # check if email backend is in settings file and return if not
    #
    if not hasattr(settings, "ANYMAIL"):
        return
    text_body = get_observation_list(False, obs_ids)

    msg = EmailMultiAlternatives(
        "SCORE Observation Upload Confirmation",
        "SCORE Observation Upload Confirmation \n\n Thank you for submitting your \
            observations. Your observations have been successfully uploaded to the \
                SCORE database.  The observation ID(s) are: \n\n"
        + text_body,
        "michelle.dadighat@noirlab.edu",
        [email_address],
    )

    email_body = "<html><h1>SCORE Observation Upload Confirmation</h1>\
                <p>Thank you for submitting your observations.  Your observations \
                have been successfully uploaded to the SCORE database. \
                The observation ID(s) are: </p>"
    email_body += get_observation_list(True, obs_ids)
    email_body += "</html>"
    msg.attach_alternative(email_body, "text/html")
    msg.send()


# Create list of observations with supplemental details for upload confirmation
def get_observation_list(is_html, obs_ids):
    list_text = ""

    for obs_id in obs_ids:
        observation = Observation.objects.get(id=obs_id)
        list_text += (
            str(obs_id)
            + " - "
            + observation.satellite_id.sat_name
            + " - "
            + str(observation.obs_time_utc)
            + "<br />"
            if is_html
            else "\n"
        )
    return list_text


# CSV header - same as upload format minus the email address for privacy
def get_csv_header():
    header = [
        "satellite_name",
        "norad_cat_id",
        "observation_time_utc",
        "observation_time_uncertainty_sec",
        "apparent_magnitude",
        "apparent_magnitude_uncertainty",
        "observer_latitude_deg",
        "observer_longitude_deg",
        "observer_altitude_m",
        "instrument",
        "observing_mode",
        "observing_filter",
        "observer_orcid",
        "satellite_right_ascension_deg",
        "satellite_right_ascension_uncertainty_deg",
        "satellite_declination_deg",
        "satellite_declination_uncertainty_deg",
        "range_to_satellite_km",
        "range_to_satellite_uncertainty_km",
        "range_rate_of_satellite_km_per_sec",
        "range_rate_of_satellite_uncertainty_km_per_sec",
        "comments",
        "data_archive_link",
    ]
    return header


def create_csv(observation_list):
    all_observations = False
    if not observation_list:
        observation_list = Observation.objects.all()
        all_observations = True

    header = get_csv_header()

    csv_lines = []
    for observation in observation_list:
        csv_lines.append(
            [
                observation.satellite_id.sat_name,
                observation.satellite_id.sat_number,
                observation.obs_time_utc,
                observation.obs_time_uncert_sec,
                observation.apparent_mag,
                observation.apparent_mag_uncert,
                observation.location_id.obs_lat_deg,
                observation.location_id.obs_long_deg,
                observation.location_id.obs_alt_m,
                observation.instrument,
                observation.obs_mode,
                observation.obs_filter,
                observation.obs_orc_id,
                observation.sat_ra_deg,
                observation.sat_dec_deg,
                observation.sat_ra_dec_uncert_deg,
                observation.range_to_sat_km,
                observation.range_to_sat_uncert_km,
                observation.range_rate_sat_km_s,
                observation.range_rate_sat_uncert_km_s,
                observation.comments,
                observation.data_archive_link,
            ]
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(csv_lines)

    zipfile_name = (
        "satellite_observations_all.zip"
        if all_observations
        else "satellite_observations_search_results.zip"
    )
    zipped_file = io.BytesIO()

    with zipfile.ZipFile(zipped_file, "w") as zip:
        zip.writestr("observations.csv", output.getvalue())
    zipped_file.seek(0)

    return zipped_file, zipfile_name
