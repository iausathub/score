import csv
import io
import zipfile
from typing import Tuple

from repository.models import Observation


# CSV header - same as upload format minus the email address for privacy
def get_csv_header() -> list[str]:
    """
    Returns the header for the CSV file.

    This function returns a list of strings representing the header of the CSV file.
    The header includes the names of all the fields in the CSV file, excluding the
    email address for privacy.

    Returns:
        list[str]: A list of strings representing the header of the CSV file.
    """
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
        "limiting_magnitude",
        "instrument",
        "observing_mode",
        "observing_filter",
        "observer_orcid",
        "satellite_right_ascension_deg",
        "satellite_declination_deg",
        "sigma_2_ra",
        "sigma_ra_sigma_dec",
        "sigma_2_dec",
        "range_to_satellite_km",
        "range_to_satellite_uncertainty_km",
        "range_rate_of_satellite_km_per_sec",
        "range_rate_of_satellite_uncertainty_km_per_sec",
        "comments",
        "data_archive_link",
        "mpc_code",
        "sat_ra_deg_satchecker",
        "sat_dec_deg_satchecker",
        "range_to_sat_km_satchecker",
        "range_rate_sat_km_s_satchecker",
        "ddec_deg_s_satchecker",
        "dra_cosdec_deg_s_satchecker",
        "phase_angle_deg_satchecker",
        "alt_deg_satchecker",
        "az_deg_satchecker",
        "illuminated",
        "international_designator",
    ]
    return header


def create_csv(
    observation_list: list[Observation], satellite_name: str
) -> Tuple[io.BytesIO, str]:
    """
    Creates a CSV file from a list of observations and compresses it into a zip file.

    This function takes a list of Observation objects, generates a CSV file with the
    details of each observation, and compresses the CSV file into a zip file. If the
    observation list is empty, it retrieves all observations from the database.
    The CSV file includes a header row with the names of all the fields.

    Args:
        observation_list (list[Observation]): A list of Observation objects.

    Returns:
        Tuple[io.BytesIO, str]: A tuple containing the compressed zip file and the
        name of the zip file.
    """
    all_observations = False
    if not observation_list:
        observation_list = Observation.objects.all()
        all_observations = True

    header = get_csv_header()

    csv_lines = []
    for observation in observation_list:
        # format ORC ID string properly - remove brackets and only have quotes around
        # the field if there is more than one ORCID separated by commas (otherwise no
        # quotes)

        if isinstance(observation.obs_orc_id, list):
            orc_id = ", ".join(observation.obs_orc_id)
        else:
            orc_id = observation.obs_orc_id.replace("[", "").replace("]", "")

        if "," in orc_id:
            orc_id = f'"{orc_id}"'

        # format date/time to match upload format
        obs_time_utc = observation.obs_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        obs_time_utc = obs_time_utc[:-4] + "Z"  # Trim to 3 digits

        csv_lines.append(
            [
                observation.satellite_id.sat_name,
                observation.satellite_id.sat_number,
                obs_time_utc,
                observation.obs_time_uncert_sec,
                observation.apparent_mag,
                observation.apparent_mag_uncert,
                observation.location_id.obs_lat_deg,
                observation.location_id.obs_long_deg,
                observation.location_id.obs_alt_m,
                observation.limiting_magnitude,
                observation.instrument,
                observation.obs_mode,
                observation.obs_filter,
                orc_id,
                observation.sat_ra_deg,
                observation.sat_dec_deg,
                observation.sigma_2_ra,
                observation.sigma_ra_sigma_dec,
                observation.sigma_2_dec,
                observation.range_to_sat_km,
                observation.range_to_sat_uncert_km,
                observation.range_rate_sat_km_s,
                observation.range_rate_sat_uncert_km_s,
                observation.comments,
                observation.data_archive_link,
                observation.mpc_code,
                observation.sat_ra_deg_satchecker,
                observation.sat_dec_deg_satchecker,
                observation.range_to_sat_km_satchecker,
                observation.range_rate_sat_km_s_satchecker,
                observation.ddec_deg_s_satchecker,
                observation.dra_cosdec_deg_s_satchecker,
                observation.phase_angle,
                observation.alt_deg_satchecker,
                observation.az_deg_satchecker,
                observation.illuminated,
                observation.satellite_id.intl_designator,
            ]
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(csv_lines)

    if satellite_name:
        zipfile_name = f"{satellite_name}_observations.zip"
    else:
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
