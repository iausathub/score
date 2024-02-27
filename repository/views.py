import csv
import datetime
import io
import logging
import zipfile
from collections import namedtuple

import requests
from astropy.time import Time
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.utils import timezone
from rest_framework.renderers import JSONRenderer

from repository.forms import SearchForm, SingleObservationForm

from .models import Location, Observation, Satellite
from .serializers import ObservationSerializer

logger = logging.getLogger(__name__)


def index(request):
    stats = get_stats()
    template = loader.get_template("repository/index.html")
    context = {
        "filename": "",
        "satellite_count": stats.satellite_count,
        "observation_count": stats.observation_count,
        "observer_count": stats.observer_count,
        "latest_obs_list": stats.latest_obs_list,
    }

    if request.method == "POST" and not request.FILES:
        context["error"] = "Please select a file to upload."
        return HttpResponse(template.render(context, request))

    if request.method == "POST" and request.FILES["uploaded_file"]:
        uploaded_file = request.FILES["uploaded_file"]
        # parse csv file into models
        data_set = uploaded_file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)
        # check if first row is header or not

        next(io_string)  # Skip the header
        obs_ids = []
        try:
            for column in csv.reader(io_string, delimiter=","):

                if "SATHUB-SATELLITE" in column[0]:
                    # fmt: off
                    context["error"] = (
                        "File contains sample data. Please upload a valid file."
                    )
                    return HttpResponse(template.render(context, request))
                    # fmt: on
                is_valid = validate_position(
                    column[0], column[1], column[2], column[6], column[7], column[8]
                )
                if is_valid is not True:
                    context["error"] = is_valid
                    return HttpResponse(template.render(context, request))

                satellite, sat_created = Satellite.objects.update_or_create(
                    sat_name=column[0],
                    sat_number=column[1],
                    constellation=column[24],
                    defaults={
                        "sat_name": column[0],
                        "sat_number": column[1],
                        "constellation": column[24],
                        "date_added": timezone.now(),
                    },
                )

                location, loc_created = Location.objects.update_or_create(
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
                observation, obs_created = Observation.objects.update_or_create(
                    obs_time_utc=column[2],
                    obs_time_uncert_sec=column[3],
                    apparent_mag=column[4],
                    apparent_mag_uncert=column[5],
                    instrument=column[9],
                    obs_mode=column[10],
                    obs_filter=column[11],
                    obs_email=column[12],
                    obs_orc_id=orc_id_list,
                    sat_ra_deg=column[14],
                    sat_ra_uncert_deg=column[15],
                    sat_dec_deg=column[16],
                    sat_dec_uncert_deg=column[17],
                    range_to_sat_km=column[18],
                    range_to_sat_uncert_km=column[19],
                    range_rate_sat_km_s=column[20],
                    range_rate_sat_uncert_km_s=column[21],
                    comments=column[22],
                    data_archive_link=column[23],
                    satellite_id=satellite,
                    location_id=location,
                    defaults={
                        "obs_time_utc": column[2],
                        "obs_time_uncert_sec": column[3],
                        "apparent_mag": column[4],
                        "apparent_mag_uncert": column[5],
                        "instrument": column[9],
                        "obs_mode": column[10],
                        "obs_filter": column[11],
                        "obs_email": column[12],
                        "obs_orc_id": orc_id_list,
                        "sat_ra_deg": column[14],
                        "sat_ra_uncert_deg": column[15],
                        "sat_dec_deg": column[16],
                        "sat_dec_uncert_deg": column[17],
                        "range_to_sat_km": column[18],
                        "range_to_sat_uncert_km": column[19],
                        "range_rate_sat_km_s": column[20],
                        "range_rate_sat_uncert_km_s": column[21],
                        "comments": column[22],
                        "data_archive_link": column[23],
                        "flag": None,
                        "satellite_id": satellite,
                        "location_id": location,
                        "date_added": timezone.now(),
                    },
                )
                logger.info(f"Uploaded observation {observation.id}")
                obs_ids.append(observation.id)
        except IndexError as e:
            context["error"] = str(e) + " - check number of fields in csv file."
            logger.exception(e)
            return HttpResponse(template.render(context, request))
        except ValueError as e:
            context["error"] = e
            logger.exception(e)
            return HttpResponse(template.render(context, request))
        except ValidationError as e:
            if len(e.messages) > 1:
                context["error"] = e.messages[1]
                logger.exception(e)
                return HttpResponse(template.render(context, request))
            else:
                message_text = ""
                for key in e.message_dict.keys():
                    message_text += f"{key}: {e.message_dict[key][0]}\n"
                context["error"] = message_text
                logger.exception(e)
                return HttpResponse(template.render(context, request))
        except Exception as e:
            context["error"] = e
            logger.exception(e)
            return HttpResponse(template.render(context, request))

        logger.info(f"Uploaded {len(obs_ids)} observations")
        context["obs_id"] = obs_ids
        context["date_added"] = datetime.datetime.now()
        return HttpResponse(template.render(context, request))
    # else:
    #     form = UploadObservationFileForm()

    context = {
        "filename": "",
        "satellite_count": stats.satellite_count,
        "observation_count": stats.observation_count,
        "observer_count": stats.observer_count,
        "latest_obs_list": stats.latest_obs_list,
    }
    return HttpResponse(template.render(context, request))


def data_format(request):
    template = loader.get_template("repository/data-format.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


def view_data(request):
    observation_list = Observation.objects.order_by("-date_added")[:500]
    observation_list_json = [
        (JSONRenderer().render(ObservationSerializer(observation).data))
        for observation in observation_list
    ]
    observations_and_json = zip(observation_list, observation_list_json)
    return render(
        request,
        "repository/view.html",
        {"observations_and_json": observations_and_json},
    )


def download_all(request):
    # create csv from observation models (All)
    header = get_csv_header()

    observations = Observation.objects.all()

    csv_lines = []
    for observation in observations:
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
                observation.sat_ra_uncert_deg,
                observation.sat_dec_deg,
                observation.sat_dec_uncert_deg,
                observation.range_to_sat_km,
                observation.range_to_sat_uncert_km,
                observation.range_rate_sat_km_s,
                observation.range_rate_sat_uncert_km_s,
                observation.comments,
                observation.data_archive_link,
                observation.satellite_id.constellation,
            ]
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(csv_lines)

    zipfile_name = "satellite_observations_all.zip"
    zipped_file = io.BytesIO()

    with zipfile.ZipFile(zipped_file, "w") as zip:
        zip.writestr("observations.csv", output.getvalue())
    zipped_file.seek(0)

    response = HttpResponse(zipped_file, content_type="application/zip")

    response["Content-Disposition"] = f"attachment; filename={zipfile_name}"
    return response


def download_obs_ids(request):
    if request.method == "POST":
        observation_ids = request.POST.get("obs_ids").split(", ")
        observation_ids = [int(i) for i in observation_ids]
        header = [
            "observation_id",
            "satellite_name",
            "date_observed",
        ]

        csv_lines = []
        for observation_id in observation_ids:
            observation = Observation.objects.get(id=observation_id)
            csv_lines.append(
                [
                    observation.id,
                    observation.satellite_id.sat_name,
                    observation.obs_time_utc,
                ]
            )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        writer.writerows(csv_lines)

        zipfile_name = "satellite_observations_ids.zip"
        zipped_file = io.BytesIO()

        with zipfile.ZipFile(zipped_file, "w") as zip:
            zip.writestr("submission.csv", output.getvalue())
        zipped_file.seek(0)

        response = HttpResponse(zipped_file, content_type="application/zip")

        response["Content-Disposition"] = f"attachment; filename={zipfile_name}"
        return response
    return HttpResponse()


def search(request):
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            sat_name = form.cleaned_data["sat_name"]
            sat_number = form.cleaned_data["sat_number"]
            obs_mode = form.cleaned_data["obs_mode"]
            start_date_range = form.cleaned_data["start_date_range"]
            end_date_range = form.cleaned_data["end_date_range"]
            constellation = form.cleaned_data["constellation"]
            observation_id = form.cleaned_data["observation_id"]
            observer_orcid = form.cleaned_data["observer_orcid"]

            # filter observations based on search criteria
            observations = Observation.objects.all()
            if sat_name:
                observations = observations.filter(
                    satellite_id__sat_name__iexact=sat_name
                )
            if sat_number:
                observations = observations.filter(satellite_id__sat_number=sat_number)
            if obs_mode:
                observations = observations.filter(obs_mode__icontains=obs_mode)
            if start_date_range:
                observations = observations.filter(obs_time_utc__gte=start_date_range)
            if end_date_range:
                observations = observations.filter(obs_time_utc__lte=end_date_range)
            if constellation:
                observations = observations.filter(
                    satellite_id__constellation__icontains=constellation
                )
            if observation_id:
                observations = observations.filter(id=observation_id)
            if observer_orcid:
                observations = observations.filter(obs_orc_id__icontains=observer_orcid)

            observation_list_json = [
                (JSONRenderer().render(ObservationSerializer(observation).data))
                for observation in observations
            ]
            observations_and_json = zip(observations, observation_list_json)
            observation_ids = [observation.id for observation in observations]

            if observations.count() == 0:
                return render(
                    request,
                    "repository/search.html",
                    {"error": "No observations found.", "form": SearchForm},
                )
            # return search results
            return render(
                request,
                "repository/search.html",
                {
                    "observations": observations_and_json,
                    "obs_ids": observation_ids,
                    "form": SearchForm,
                },
            )
        else:
            return render(request, "repository/search.html", {"form": form})

    return render(request, "repository/search.html", {"form": SearchForm})


def download_results(request):
    if request.method == "POST":
        observation_ids = request.POST.get("obs_ids").split(", ")
        observation_ids = [int(i.strip("[]")) for i in observation_ids]

        observations = Observation.objects.filter(id__in=observation_ids)
        # create csv from observation models (All)
        header = get_csv_header()

        csv_lines = []
        for observation in observations:
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
                    observation.sat_ra_uncert_deg,
                    observation.sat_dec_deg,
                    observation.sat_dec_uncert_deg,
                    observation.range_to_sat_km,
                    observation.range_to_sat_uncert_km,
                    observation.range_rate_sat_km_s,
                    observation.range_rate_sat_uncert_km_s,
                    observation.comments,
                    observation.data_archive_link,
                    observation.satellite_id.constellation,
                ]
            )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        writer.writerows(csv_lines)

        zipfile_name = "satellite_observations_search_results.zip"
        zipped_file = io.BytesIO()

        with zipfile.ZipFile(zipped_file, "w") as zip:
            zip.writestr("observations.csv", output.getvalue())
        zipped_file.seek(0)

        response = HttpResponse(zipped_file, content_type="application/zip")

        response["Content-Disposition"] = f"attachment; filename={zipfile_name}"
        return response
    return HttpResponse()


def upload(request):
    if request.method == "POST":
        form = SingleObservationForm(request.POST)
        if form.is_valid():
            orc_id_list = [
                orc_id.strip()
                for orc_id in form.cleaned_data["observer_orcid"].split(",")
            ]

            sat_name = form.cleaned_data["sat_name"]
            sat_number = form.cleaned_data["sat_number"]
            obs_mode = form.cleaned_data["obs_mode"]
            obs_date = form.cleaned_data["obs_date"]
            obs_date_uncert = form.cleaned_data["obs_date_uncert"]
            apparent_mag = form.cleaned_data["apparent_mag"]
            apparent_mag_uncert = form.cleaned_data["apparent_mag_uncert"]
            instrument = form.cleaned_data["instrument"]
            filter = form.cleaned_data["filter"]
            observer_email = form.cleaned_data["observer_email"]
            constellation = form.cleaned_data["constellation"]
            observer_orcid = orc_id_list
            obs_lat_deg = form.cleaned_data["observer_latitude_deg"]
            obs_long_deg = form.cleaned_data["observer_longitude_deg"]
            obs_alt_m = form.cleaned_data["observer_altitude_m"]
            sat_ra_deg = form.cleaned_data["sat_ra_deg"]
            sat_ra_uncert_deg = form.cleaned_data["sat_ra_uncert_deg"]
            sat_dec_deg = form.cleaned_data["sat_dec_deg"]
            sat_dec_uncert_deg = form.cleaned_data["sat_dec_uncert_deg"]
            range_to_sat_km = form.cleaned_data["range_to_sat_km"]
            range_to_sat_uncert_km = form.cleaned_data["range_to_sat_uncert_km"]
            range_rate_sat_km_s = form.cleaned_data["range_rate_sat_km_s"]
            range_rate_sat_uncert_km_s = form.cleaned_data["range_rate_sat_uncert_km_s"]
            comments = form.cleaned_data["comments"]
            data_archive_link = form.cleaned_data["data_archive_link"]

            satellite, sat_created = Satellite.objects.update_or_create(
                sat_name=sat_name,
                sat_number=sat_number,
                constellation=constellation,
                defaults={
                    "sat_name": sat_name,
                    "sat_number": sat_number,
                    "constellation": constellation,
                    "date_added": timezone.now(),
                },
            )

            location, loc_created = Location.objects.update_or_create(
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

            observation, obs_created = Observation.objects.update_or_create(
                obs_time_utc=obs_date,
                obs_time_uncert_sec=obs_date_uncert,
                apparent_mag=apparent_mag,
                apparent_mag_uncert=apparent_mag_uncert,
                instrument=instrument,
                obs_mode=obs_mode,
                obs_filter=filter,
                obs_email=observer_email,
                obs_orc_id=observer_orcid,
                sat_ra_deg=sat_ra_deg,
                sat_ra_uncert_deg=sat_ra_uncert_deg,
                sat_dec_deg=sat_dec_deg,
                sat_dec_uncert_deg=sat_dec_uncert_deg,
                range_to_sat_km=range_to_sat_km,
                range_to_sat_uncert_km=range_to_sat_uncert_km,
                range_rate_sat_km_s=range_rate_sat_km_s,
                range_rate_sat_uncert_km_s=range_rate_sat_uncert_km_s,
                comments=comments,
                data_archive_link=data_archive_link,
                satellite_id=satellite,
                location_id=location,
                defaults={
                    "obs_time_utc": obs_date,
                    "obs_time_uncert_sec": obs_date_uncert,
                    "apparent_mag": apparent_mag,
                    "apparent_mag_uncert": apparent_mag_uncert,
                    "instrument": instrument,
                    "obs_mode": obs_mode,
                    "obs_filter": filter,
                    "obs_email": observer_email,
                    "obs_orc_id": observer_orcid,
                    "sat_ra_deg": sat_ra_deg,
                    "sat_ra_uncert_deg": sat_ra_uncert_deg,
                    "sat_dec_deg": sat_dec_deg,
                    "sat_dec_uncert_deg": sat_dec_uncert_deg,
                    "range_to_sat_km": range_to_sat_km,
                    "range_to_sat_uncert_km": range_to_sat_uncert_km,
                    "range_rate_sat_km_s": range_rate_sat_km_s,
                    "range_rate_sat_uncert_km_s": range_rate_sat_uncert_km_s,
                    "comments": comments,
                    "data_archive_link": data_archive_link,
                    "flag": None,
                    "satellite_id": satellite,
                    "location_id": location,
                    "date_added": timezone.now(),
                },
            )

            obs_id = observation.id
            # confirm observation uploaded
            return render(
                request,
                "repository/upload-obs.html",
                {
                    "status": "Upload successful",
                    "obs_id": obs_id,
                    "obs_email": observer_email,
                    "form": SingleObservationForm,
                },
            )
        else:
            return render(request, "repository/upload-obs.html", {"form": form})

    return render(
        request, "repository/upload-obs.html", {"form": SingleObservationForm}
    )


def about(request):
    template = loader.get_template("repository/about.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


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

    observation_list_json = [
        (JSONRenderer().render(ObservationSerializer(observation).data))
        for observation in latest_obs_list
    ]
    observations_and_json = zip(latest_obs_list, observation_list_json)

    return stats(
        satellite_count, observation_count, observer_count, observations_and_json
    )


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
        "constellation",
    ]
    return header


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
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200 or not r.json():
        return "Satellite not visible at this time and location"
    if r.json()[0]["NAME"] != satellite_name:
        return "Satellite name and number do not match"
    if float(r.json()[0]["ALTITUDE-DEG"]) < -5:
        return "Satellite below horizon"
    return True
