from typing import Any, Union

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.forms import ValidationError
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils import add_additional_data, send_confirmation_email


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
    try:
        for column in data:
            # Check for data from the sample CSV file
            if "SATHUB-SATELLITE" in column[0]:
                raise UploadError(
                    "File contains sample data. Please upload a valid file."
                )

            if len(column) != 27:
                raise UploadError("Incorrect number of fields in csv file.")

            # Check if satellite is above the horizon
            additional_data = add_additional_data(
                column[0], column[1], column[2], column[6], column[7], column[8]
            )

            obs_error_reference = (
                "Observation: " + column[0] + " " + column[1] + " " + column[2]
            )

            if isinstance(additional_data, str):
                raise UploadError(additional_data + " - " + obs_error_reference)

            satellite, sat_created = Satellite.objects.get_or_create(
                sat_name=column[0],
                sat_number=column[1],
                defaults={
                    "sat_name": column[0],
                    "sat_number": column[1],
                    "date_added": timezone.now(),
                },
            )
            location, loc_created = Location.objects.get_or_create(
                obs_lat_deg=column[6],
                obs_long_deg=column[7],
                obs_alt_m=column[8],
                defaults={
                    "obs_lat_deg": column[6],
                    "obs_long_deg": column[7],
                    "obs_alt_m": column[8],
                    "date_added": timezone.now(),
                },
            )

            orc_id_list = [item.strip() for item in column[14].split(",")]
            if column[4] == "" and column[5] == "":
                column[4] = None
                column[5] = None

            observation, obs_created = Observation.objects.get_or_create(
                obs_time_utc=column[2],
                obs_time_uncert_sec=column[3],
                apparent_mag=column[4],
                apparent_mag_uncert=column[5],
                limiting_magnitude=column[9],
                instrument=column[10],
                obs_mode=column[11].upper(),
                obs_filter=column[12],
                obs_email=column[13],
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
                    "obs_email": column[13],
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
        raise UploadError(str(e)) from e

    except ValidationError as e:
        if len(e.messages) > 1:
            raise UploadError(e.messages[1]) from e

        else:
            message_text = ""
            for key in e.message_dict.keys():
                message_text += f"{key}: {e.message_dict[key][0]}\n"
            raise UploadError(message_text) from e

    except Exception as e:
        raise UploadError(e) from e

    send_confirmation_email(obs_ids, confirmation_email)

    current_date = timezone.now().isoformat()
    return {
        "status": "success",
        "obs_ids": obs_ids,
        "date_added": current_date,
        "email": confirmation_email,
    }
