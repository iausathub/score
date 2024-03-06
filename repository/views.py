import csv
import datetime
import io
import zipfile
from collections import namedtuple

from django.db.models import Avg
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from repository.forms import SearchForm

from .models import Location, Observation, Satellite


def index(request):
    if request.method == "POST" and not request.FILES:
        return render(
            request,
            "repository/index.html",
            {"error": "Please select a file to upload."},
        )
    if request.method == "POST" and request.FILES["uploaded_file"]:
        uploaded_file = request.FILES["uploaded_file"]
        # parse csv file into models
        data_set = uploaded_file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)
        # check if first row is header or not

        next(io_string)  # Skip the header
        obs_ids = []
        try:

            for column in csv.reader(io_string, delimiter=",", quotechar="|"):
                satellite, sat_created = Satellite.objects.update_or_create(
                    sat_name=column[0],
                    sat_number=column[1],
                    constellation=column[24],
                    defaults={
                        "sat_name": column[0],
                        "sat_number": column[1],
                        "constellation": column[24],
                        "date_added": datetime.datetime.now(),
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
                        "date_added": datetime.datetime.now(),
                    },
                )

                observation, obs_created = Observation.objects.update_or_create(
                    obs_time_utc=column[2],
                    obs_time_uncert_sec=column[3],
                    apparent_mag=column[4],
                    apparent_mag_uncert=column[5],
                    instrument=column[9],
                    obs_mode=column[10],
                    obs_filter=column[11],
                    obs_email=column[12],
                    obs_orc_id=column[13],
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
                        "obs_orc_id": column[13],
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
                        "date_added": datetime.datetime.now(),
                    },
                )
                obs_ids.append(observation.id)

        except ValueError as e:
            return render(request, "repository/index.html", {"error": e})
        except ValidationError as e:
            if len(e.messages) > 1:
                return render(
                    request, "repository/index.html", {"error": e.messages[1]}
                )
            else:
                message_text = ""
                for key in e.message_dict.keys():
                    message_text += f"{key}: {e.message_dict[key][0]}\n"

                return render(request, "repository/index.html", {"error": message_text})
            return render(request, "repository/index.html", {"error": e.messages[0]})
        stats = get_stats()
        return render(
            request,
            "repository/index.html",
            {
                "obs_id": obs_ids,
                "satellite_count": stats.satellite_count,
                "observation_count": stats.observation_count,
                "observer_count": stats.observer_count,
                "latest_obs_list": stats.latest_obs_list,
                "avg_mag": stats.avg_mag,
            },
        )
    # else:
    #     form = UploadObservationFileForm()
    stats = get_stats()
    template = loader.get_template("repository/index.html")
    context = {
        "filename": "",
        "satellite_count": stats.satellite_count,
        "observation_count": stats.observation_count,
        "observer_count": stats.observer_count,
        "latest_obs_list": stats.latest_obs_list,
        "avg_mag": stats.avg_mag,
    }
    return HttpResponse(template.render(context, request))


def data_format(request):
    template = loader.get_template("repository/data-format.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


def view_data(request):
    observation_list = Observation.objects.all()
    return render(request, "repository/view.html", {"observations": observation_list})


def download_all(request):
    # create csv from observation models (All)
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
        "observer_email",
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
                observation.obs_email,
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

            # filter observations based on search criteria
            observations = Observation.objects.all()
            if sat_name:
                observations = observations.filter(
                    satellite_id__sat_name__icontains=sat_name
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
                {"observations": observations, "form": SearchForm},
            )
        # handle search form
        return render(request, "repository/search.html", {"form": SearchForm})

    return render(request, "repository/search.html", {"form": SearchForm})


def download_results(request):
    # create csv from observation models (All)
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
        "observer_email",
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

    observations = []

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
                observation.obs_email,
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


def get_stats():
    stats = namedtuple(
        "stats",
        [
            "satellite_count",
            "observation_count",
            "observer_count",
            "latest_obs_list",
            "avg_mag",
        ],
    )

    satellite_count = Satellite.objects.count()
    observation_count = Observation.objects.count()
    observer_count = (
        Observation.objects.values("location_id", "obs_email").distinct().count()
    )
    latest_obs_list = Observation.objects.order_by("-date_added")[:7]
    avg_mag = float(
        "{:.2f}".format(
            Observation.objects.aggregate(Avg("apparent_mag"))["apparent_mag__avg"]
        )
    )

    return stats(
        satellite_count, observation_count, observer_count, latest_obs_list, avg_mag
    )
