import csv
import datetime
import io
import logging
import zipfile
from typing import Union

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer

from repository.forms import DataChangeForm, SearchForm, SingleObservationForm
from repository.tasks import process_upload
from repository.utils import (
    add_additional_data,
    create_csv,
    get_stats,
    send_confirmation_email,
    send_data_change_email,
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

    return HttpResponse(template.render(context, request))


def data_format(request):
    template = loader.get_template("repository/data-format.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


def view_data(request) -> HttpResponse:
    """
    Show the 500 most recent observations and render the 'repository/view.html'
    template.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The HttpResponse object with the rendered template.
    """
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


def download_all(request) -> HttpResponse:
    """
    Create a CSV file, zip it, and return it as a downloadable file.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The HttpResponse object with the zipped CSV file.
    """
    if request.method == "POST" and settings.RECAPTCHA_PUBLIC_KEY != "":
        # Get the reCAPTCHA response from the POST data
        recaptcha_response = request.POST.get("g-recaptcha-response")

        data = {
            "secret": settings.RECAPTCHA_PRIVATE_KEY,
            "response": recaptcha_response,
        }

        # Send a POST request to the Google reCAPTCHA API
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify", data=data, timeout=30
        )

        # Get the result
        result = r.json()

        # If the reCAPTCHA was valid, proceed with the download
        if result["score"] > 0.7:
            return create_and_return_csv(False)
        else:
            # If the reCAPTCHA was not valid, return an error message
            return JsonResponse({"error": "Invalid reCAPTCHA. Please try again."})
    # If reCAPTCHA is not enabled (development mode), proceed with the download
    else:
        return create_and_return_csv(False)


def create_and_return_csv(observations: Union[list[Observation], bool]) -> HttpResponse:
    """
    Create a CSV file from the provided observations and return it as a zipped file
    in an HTTP response.

    Args:
        observations (Union[List[Observation], bool]): A list of Observation objects
        or False. If false, all observations will be included in the CSV file.

    Returns:
        HttpResponse: An HTTP response containing the zipped CSV file. The Content-Type
        of the response is set to "application/zip", and the Content-Disposition is set
        to make the file a download with the appropriate filename.
    """
    zipped_file, zipfile_name = create_csv(observations)
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
            "satellite_number",
            "date_observed",
        ]

        csv_lines = []
        for observation_id in observation_ids:
            observation = Observation.objects.get(id=observation_id)
            csv_lines.append(
                [
                    observation.id,
                    observation.satellite_id.sat_name,
                    observation.satellite_id.sat_number,
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
            mpc_code = form.cleaned_data["mpc_code"]

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
            if observation_id:
                observations = observations.filter(id=observation_id)
            if observer_orcid:
                observations = observations.filter(obs_orc_id__icontains=observer_orcid)
            if mpc_code:
                observations = observations.filter(mpc_code=mpc_code)

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

        return create_and_return_csv(observations)

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
            limiting_magnitude = form.cleaned_data["limiting_magnitude"]
            comments = form.cleaned_data["comments"]
            data_archive_link = form.cleaned_data["data_archive_link"]
            mpc_code = form.cleaned_data["mpc_code"]

            # Check if satellite is above the horizon
            additional_data = add_additional_data(
                sat_name, sat_number, obs_date, obs_lat_deg, obs_long_deg, obs_alt_m
            )
            if isinstance(additional_data, str):
                return render(
                    request,
                    "repository/upload-obs.html",
                    {"form": form, "error": additional_data},
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
                mpc_code=mpc_code.strip().upper() if mpc_code else None,
                limiting_magnitude=limiting_magnitude,
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
                    "limiting_magnitude": limiting_magnitude,
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
                    "comments": comments,
                    "data_archive_link": data_archive_link,
                    "mpc_code": mpc_code.strip().upper() if mpc_code else None,
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
    context = {
        "recaptcha_public_key": settings.RECAPTCHA_PUBLIC_KEY,
    }
    return HttpResponse(template.render(context, request))


def data_change(request):
    if request.method == "POST":
        form = DataChangeForm(request.POST)
        if form.is_valid():
            contact_email = form.cleaned_data["contact_email"]
            obs_ids = form.cleaned_data["obs_ids"]
            reason = form.cleaned_data["reason"]

            # Send the confirmation email
            send_data_change_email(contact_email, obs_ids, reason)
            return render(
                request,
                "repository/data-change.html",
                {
                    "msg": "Your request has been submitted. "
                    "You will receive an email confirmation "
                    "when your request is reviewed.",
                    "form": DataChangeForm,
                },
            )
    else:
        form = DataChangeForm()

    return render(request, "repository/data-change.html", {"form": DataChangeForm})


@csrf_exempt
def last_observer_location(request):
    """
    This view returns the last location of an observer based on the provided ORCID.

    The ORCID is received from a POST request. If the ORCID is valid and there are
    observations associated with it, the function returns a JSON response with the
    latitude, longitude, and altitude of the observer's last location.

    If the ORCID is not valid/complete or there are no observations associated with it,
    the function returns a JSON response with an error message.

    Parameters:
    request (HttpRequest): The Django request object.

    Returns:
    JsonResponse: A JSON response with the observer's last location or an error message.
    """
    observer_orcid = request.POST.get("observer_orcid")
    if len(observer_orcid) != 19:
        return JsonResponse(
            {
                "error": "pass",
            }
        )
    if observer_orcid:
        observer = (
            Observation.objects.filter(obs_orc_id__icontains=observer_orcid)
            .order_by("-date_added")
            .first()
        )
        if observer:
            return JsonResponse(
                {
                    "observer_latitude_deg": observer.location_id.obs_lat_deg,
                    "observer_longitude_deg": observer.location_id.obs_long_deg,
                    "observer_altitude_m": observer.location_id.obs_alt_m,
                }
            )

    return JsonResponse(
        {
            "error": "No observations found for the provided ORCID.",
        }
    )
