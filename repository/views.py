import csv
import datetime
import io
import logging
import zipfile

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.utils import timezone
from rest_framework.renderers import JSONRenderer

from repository.forms import SearchForm, SingleObservationForm
from repository.tasks import process_upload
from repository.utils import (
    create_csv,
    get_stats,
    send_confirmation_email,
    validate_position,
)

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

    # Handle file upload
    if request.method == "POST" and request.FILES["uploaded_file"]:
        uploaded_file = request.FILES["uploaded_file"]

        data_set = uploaded_file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)

        # Skip the header if it exists
        first_line = next(io_string)
        if first_line.startswith("satellite_name"):
            pass
        else:
            io_string.seek(0)

        read_data = csv.reader(io_string, delimiter=",")
        obs = list(read_data)

        # Create Task
        upload_task = process_upload.delay(obs)
        task_id = upload_task.task_id

        context["task_id"] = task_id

        context["date_added"] = datetime.datetime.now()
        return HttpResponse(template.render(context, request))

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
    # Show the 500 most recent observations
    observation_list = Observation.objects.order_by("-date_added")[:500]

    # JSON is also needed for the modal view to show the observation details
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
    zipped_file, zipfile_name = create_csv(False)
    response = HttpResponse(zipped_file, content_type="application/zip")

    response["Content-Disposition"] = f"attachment; filename={zipfile_name}"
    return response


def download_obs_ids(request):
    # Provide the observation IDs for the observations that were just uploaded
    # with the satellite name and date observed for context (CSV)
    if request.method == "POST":
        observation_ids = request.POST.get("obs_ids").split(",")

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

        zipfile_name = "satellite_observation_ids.zip"
        zipped_file = io.BytesIO()

        with zipfile.ZipFile(zipped_file, "w") as zip:
            zip.writestr("satellite_observation_ids.csv", output.getvalue())
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
            if observation_id:
                observations = observations.filter(id=observation_id)
            if observer_orcid:
                observations = observations.filter(obs_orc_id__icontains=observer_orcid)

            # JSON is also needed for the modal view to show the observation details
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
    # Download the search results as a CSV file
    if request.method == "POST":
        observation_ids = request.POST.get("obs_ids").split(", ")
        observation_ids = [int(i.strip("[]")) for i in observation_ids]

        observations = Observation.objects.filter(id__in=observation_ids)

        zipped_file, zipfile_name = create_csv(observations)
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
            observer_orcid = orc_id_list
            obs_lat_deg = form.cleaned_data["observer_latitude_deg"]
            obs_long_deg = form.cleaned_data["observer_longitude_deg"]
            obs_alt_m = form.cleaned_data["observer_altitude_m"]
            sat_ra_deg = form.cleaned_data["sat_ra_deg"]
            sat_dec_deg = form.cleaned_data["sat_dec_deg"]
            sat_ra_dec_uncert_deg = form.cleaned_data["sat_ra_dec_uncert_deg"]
            range_to_sat_km = form.cleaned_data["range_to_sat_km"]
            range_to_sat_uncert_km = form.cleaned_data["range_to_sat_uncert_km"]
            range_rate_sat_km_s = form.cleaned_data["range_rate_sat_km_s"]
            range_rate_sat_uncert_km_s = form.cleaned_data["range_rate_sat_uncert_km_s"]
            comments = form.cleaned_data["comments"]
            data_archive_link = form.cleaned_data["data_archive_link"]

            # Check if satellite is above the horizon
            is_valid = validate_position(
                sat_name, sat_number, obs_date, obs_lat_deg, obs_long_deg, obs_alt_m
            )
            if is_valid is not True:
                return render(
                    request,
                    "repository/upload-obs.html",
                    {"form": form, "error": is_valid},
                )

            satellite, sat_created = Satellite.objects.get_or_create(
                sat_name=sat_name,
                sat_number=sat_number,
                defaults={
                    "sat_name": sat_name,
                    "sat_number": sat_number,
                    "date_added": timezone.now(),
                },
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

            observation, obs_created = Observation.objects.get_or_create(
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
                sat_dec_deg=sat_dec_deg,
                sat_ra_dec_uncert_deg=(
                    [float(x) for x in sat_ra_dec_uncert_deg.split(",")]
                    if sat_ra_dec_uncert_deg
                    else []
                ),
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
                    "sat_dec_deg": sat_dec_deg,
                    "sat_ra_dec_uncert_deg": (
                        [float(x) for x in sat_ra_dec_uncert_deg.split(",")]
                        if sat_ra_dec_uncert_deg
                        else []
                    ),
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
            send_confirmation_email([obs_id], observer_email)

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


def download_data(request):
    template = loader.get_template("repository/download-data.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))
