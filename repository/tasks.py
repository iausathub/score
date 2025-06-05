from typing import Any, Union

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.forms import ValidationError
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils.email_utils import send_confirmation_email
from repository.utils.general_utils import add_additional_data


class UploadError(Exception):
    pass


@shared_task(bind=True)
def process_upload(
    self, data: list[list[Any]]
) -> dict[str, Union[str, list[int], bool]]:
    """
    Processes the uploaded CSV data and creates or updates the corresponding Satellite,
    Location, and Observation objects.

    This function takes a list of lists where each inner list represents a row from
    the CSV file. It validates the data, creates or updates the corresponding Satellite,
    Location, and Observation objects, and sends a confirmation email.

    Args:
        data (list[list[str]]): A list of lists where each inner list represents a row
                                from the CSV file.

    Returns:
        dict[str, object]: A dictionary containing the status of the upload, the IDs of
        the created or updated observations, the date the upload was added, and the
        email to which the confirmation was sent.
    """
    progress_recorder = ProgressRecorder(self)

    obs_ids = []

    observation_count = len(data)
    obs_num = 0
    confirmation_email = False
    obs_error_reference = None

    try:
        for column in data:
            # Check for data from the sample CSV file
            if "SATHUB-SATELLITE" in column[0]:
                raise UploadError(
                    "File contains sample data. Please upload a valid file."
                )

            if len(column) != 27:
                raise UploadError(
                    f"Incorrect number of fields in csv file: expected 27, got {len(column)}."  # noqa: E501
                )

            # Satellite names are always upper case for some reason
            column[0] = column[0].upper()
            # Check if satellite is above the horizon
            additional_data = add_additional_data(
                column[0],
                column[1],
                column[2],
                float(column[6]),
                float(column[7]),
                float(column[8]),
            )

            # This gives the format
            # Observation x/y: satellite_name sat_number obs_time_utc
            obs_error_reference = (
                f"Observation {obs_num + 1}/{observation_count}: "
                f"{column[0]} {str(column[1])} {column[2]}"
            )

            if isinstance(additional_data, str):
                raise UploadError(additional_data + " - " + obs_error_reference)

            # Special error message cases
            if column[4] == "" and column[5] != "":
                error_message = (
                    "Apparent magnitude uncertainty without apparent magnitude."
                )
                raise UploadError(error_message + " - " + obs_error_reference)

            try:
                obs_lat_deg = float(column[6])
                obs_long_deg = float(column[7])
                obs_alt_m = float(column[8])
            except ValueError as e:
                raise UploadError(
                    f"Invalid value: {str(e)} - {obs_error_reference}"
                ) from e

            # First try to get existing satellite by number
            try:
                satellite = Satellite.objects.get(sat_number=column[1])
                # Get the new name from either column[0] or additional_data
                new_name = (
                    column[0] if column[0] != "" else additional_data.satellite_name
                )

                # Update name if:
                # 1. Satellite has no name and new data has a name, OR
                # 2. New data has a name that's different from current satellite name
                if (not satellite.sat_name and new_name) or (
                    new_name and new_name != satellite.sat_name
                ):
                    satellite.sat_name = new_name
                    satellite.save()

                # If satellite exists but has no intl_designator, update it
                if not satellite.intl_designator and additional_data.intl_designator:
                    satellite.intl_designator = additional_data.intl_designator
                    satellite.save()

            except Satellite.DoesNotExist:
                # Only create new satellite if it doesn't exist
                satellite = Satellite.objects.create(
                    sat_name=(
                        column[0] if column[0] != "" else additional_data.satellite_name
                    ),
                    sat_number=column[1],
                    date_added=timezone.now(),
                    intl_designator=additional_data.intl_designator,
                )

            location, loc_created = Location.objects.get_or_create(
                obs_lat_deg=obs_lat_deg,
                obs_long_deg=obs_long_deg,
                obs_alt_m=obs_alt_m,
                defaults={
                    "obs_lat_deg": obs_lat_deg,
                    "obs_long_deg": obs_long_deg,
                    "obs_alt_m": obs_alt_m,
                    "date_added": timezone.now(),
                },
            )

            orc_id_list = [item.strip() for item in column[14].split(",")]
            if column[4] == "" and column[5] == "":
                column[4] = None
                column[5] = None

            # Remove whitespace
            observer_email = column[13].strip().lower()
            observer_email = "".join(observer_email.split())

            observation, obs_created = Observation.objects.get_or_create(
                obs_time_utc=column[2],
                obs_time_uncert_sec=column[3],
                apparent_mag=column[4],
                apparent_mag_uncert=column[5],
                limiting_magnitude=column[9],
                instrument=column[10],
                obs_mode=column[11].upper(),
                obs_filter=column[12],
                obs_email=observer_email,
                obs_orc_id=orc_id_list,
                sat_ra_deg=column[15] if column[15] else None,
                sat_dec_deg=column[16] if column[16] else None,
                sigma_2_ra=column[17] if column[17] else None,
                sigma_ra_sigma_dec=column[18] if column[18] else None,
                sigma_2_dec=column[19] if column[19] else None,
                range_to_sat_km=column[20] if column[20] else None,
                range_to_sat_uncert_km=column[21] if column[21] else None,
                range_rate_sat_km_s=column[22] if column[22] else None,
                range_rate_sat_uncert_km_s=column[23] if column[23] else None,
                comments=column[24],
                data_archive_link=column[25],
                mpc_code=column[26].strip().upper() if column[26] else None,
                phase_angle=additional_data.phase_angle,
                range_to_sat_km_satchecker=additional_data.range_to_sat,
                range_rate_sat_km_s_satchecker=additional_data.range_rate,
                sat_ra_deg_satchecker=additional_data.sat_ra_deg,
                sat_dec_deg_satchecker=additional_data.sat_dec_deg,
                ddec_deg_s_satchecker=additional_data.ddec_deg_s,
                dra_cosdec_deg_s_satchecker=additional_data.dra_cosdec_deg_s,
                alt_deg_satchecker=additional_data.alt_deg,
                az_deg_satchecker=additional_data.az_deg,
                illuminated=additional_data.illuminated,
                satellite_id=satellite,
                location_id=location,
                defaults={
                    "obs_time_utc": column[2],
                    "obs_time_uncert_sec": column[3],
                    "apparent_mag": column[4],
                    "apparent_mag_uncert": column[5],
                    "limiting_magnitude": column[9],
                    "instrument": column[10],
                    "obs_mode": column[11].upper(),
                    "obs_filter": column[12],
                    "obs_email": observer_email,
                    "obs_orc_id": orc_id_list,
                    "sat_ra_deg": column[15] if column[15] else None,
                    "sat_dec_deg": column[16] if column[16] else None,
                    "sigma_2_ra": column[17] if column[17] else None,
                    "sigma_ra_sigma_dec": column[18] if column[18] else None,
                    "sigma_2_dec": column[19] if column[19] else None,
                    "range_to_sat_km": column[20] if column[20] else None,
                    "range_to_sat_uncert_km": column[21] if column[21] else None,
                    "range_rate_sat_km_s": column[22] if column[22] else None,
                    "range_rate_sat_uncert_km_s": column[23] if column[23] else None,
                    "comments": column[24],
                    "data_archive_link": column[25],
                    "mpc_code": column[26].strip().upper() if column[26] else None,
                    "phase_angle": additional_data.phase_angle,
                    "range_to_sat_km_satchecker": additional_data.range_to_sat,
                    "range_rate_sat_km_s_satchecker": additional_data.range_rate,
                    "sat_ra_deg_satchecker": additional_data.sat_ra_deg,
                    "sat_dec_deg_satchecker": additional_data.sat_dec_deg,
                    "ddec_deg_s_satchecker": additional_data.ddec_deg_s,
                    "dra_cosdec_deg_s_satchecker": additional_data.dra_cosdec_deg_s,
                    "alt_deg_satchecker": additional_data.alt_deg,
                    "az_deg_satchecker": additional_data.az_deg,
                    "illuminated": additional_data.illuminated,
                    "flag": None,
                    "satellite_id": satellite,
                    "location_id": location,
                    "date_added": timezone.now(),
                },
            )

            obs_ids.append(observation.id)
            if not confirmation_email:
                confirmation_email = column[13]
            progress_recorder.set_progress(
                obs_num + 1, observation_count, description=""
            )
            obs_num += 1
    except IndexError as e:
        raise UploadError(str(e) + " - check number of fields in csv file.") from e

    except ValueError as e:
        error_message = str(e)
        if obs_error_reference:
            error_message += " - " + obs_error_reference
        raise UploadError(error_message) from e

    except ValidationError as e:
        if hasattr(e, "message_dict"):
            error_message = ""
            if obs_error_reference:
                error_message += obs_error_reference + " - "
            for field, messages in e.message_dict.items():
                if field == "__all__":
                    error_message += "Notes: "
                else:
                    error_message += f"Field '{field}':"
                for message in messages:
                    error_message += f" {message}"
                error_message += "\n"
            raise UploadError(error_message) from e
        else:
            if len(e.messages) > 1:
                error_message = ""
                if obs_error_reference:
                    error_message += obs_error_reference + " - "
                for message in e.messages:
                    error_message += message + "\n"
                raise UploadError(error_message) from e
            else:
                raise UploadError(e.messages[0]) from e

    except Exception as e:
        if obs_error_reference and obs_error_reference not in str(e):
            print(f"obs_error_reference: {obs_error_reference}")
            raise UploadError(str(e) + " - " + obs_error_reference) from e
        else:
            raise UploadError(str(e)) from e

    send_confirmation_email(obs_ids, confirmation_email)

    current_date = timezone.now().isoformat()
    return {
        "status": "success",
        "obs_ids": obs_ids,
        "date_added": current_date,
        "email": confirmation_email,
    }
