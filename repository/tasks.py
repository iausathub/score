from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.forms import ValidationError
from django.utils import timezone

from repository.models import Location, Observation, Satellite
from repository.utils import send_confirmation_email, validate_position


class UploadError(Exception):
    pass


@shared_task(bind=True)
def ProcessUpload(self, data):  # noqa: N802
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

            # Check if satellite is above the horizon
            is_valid = validate_position(
                column[0], column[1], column[2], column[6], column[7], column[8]
            )
            if is_valid is not True:
                raise UploadError(is_valid)

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
            orc_id_list = [item.strip() for item in column[13].split(",")]
            if column[4] == "" and column[5] == "":
                column[4] = None
                column[5] = None
            observation, obs_created = Observation.objects.get_or_create(
                obs_time_utc=column[2],
                obs_time_uncert_sec=column[3],
                apparent_mag=column[4],
                apparent_mag_uncert=column[5],
                instrument=column[9],
                obs_mode=column[10].upper(),
                obs_filter=column[11],
                obs_email=column[12],
                obs_orc_id=orc_id_list,
                sat_ra_deg=column[14],
                sat_dec_deg=column[15],
                sat_ra_dec_uncert_deg=[float(x) for x in column[16].split(",")],
                range_to_sat_km=column[17],
                range_to_sat_uncert_km=column[18],
                range_rate_sat_km_s=column[19],
                range_rate_sat_uncert_km_s=column[20],
                comments=column[21],
                data_archive_link=column[22],
                satellite_id=satellite,
                location_id=location,
                defaults={
                    "obs_time_utc": column[2],
                    "obs_time_uncert_sec": column[3],
                    "apparent_mag": column[4],
                    "apparent_mag_uncert": column[5],
                    "instrument": column[9],
                    "obs_mode": column[10].upper(),
                    "obs_filter": column[11],
                    "obs_email": column[12],
                    "obs_orc_id": orc_id_list,
                    "sat_ra_deg": column[14],
                    "sat_dec_deg": column[15],
                    "sat_ra_dec_uncert_deg": [float(x) for x in column[16].split(",")],
                    "range_to_sat_km": column[17],
                    "range_to_sat_uncert_km": column[18],
                    "range_rate_sat_km_s": column[19],
                    "range_rate_sat_uncert_km_s": column[20],
                    "comments": column[21],
                    "data_archive_link": column[22],
                    "flag": None,
                    "satellite_id": satellite,
                    "location_id": location,
                    "date_added": timezone.now(),
                },
            )
            obs_ids.append(observation.id)
            if not confirmation_email:
                confirmation_email = column[12]
            progress_recorder.set_progress(
                obs_num + 1, observation_count, description=""
            )
            obs_num += 1
    except IndexError as e:
        raise UploadError(str(e) + " - check number of fields in csv file.") from e

    except ValueError as e:
        raise UploadError(e) from e

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
