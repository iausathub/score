import csv
import datetime
import io
import logging
import zipfile
from typing import Union

import requests
from astropy.time import Time
from celery.result import AsyncResult
from django.conf import settings
from django.db.models import Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer

from repository.forms import (
    DataChangeForm,
    GenerateCSVForm,
    SearchForm,
)
from repository.tasks import process_upload
from repository.utils import (
    create_csv,
    get_norad_id,
    get_satellite_name,
    get_stats,
    send_data_change_email,
)

from .models import Observation, Satellite
from .serializers import ObservationSerializer

logger = logging.getLogger(__name__)


def temp_health_check(request):
    return HttpResponse("OK", status=200)


def custom_404(request, exception):
    return render(request, "404.html", status=404)


def index(request):
    stats = get_stats()
    template = loader.get_template("repository/index.html")

    context = {
        "filename": "",
        "satellite_count": stats.satellite_count,
        "observation_count": stats.observation_count,
        "observer_count": stats.observer_count,
        "latest_obs_list": stats.latest_obs_list,
        "observer_locations": stats.observer_locations,
    }

    # Make sure that the progress bar is shown only if the page was redirected
    # right after task creation -- remove the task id after so that it doesn't
    # stick around when the page is manually refreshed
    if "recent" in request.session and "task_id" in request.session:
        task_id = request.session["task_id"]
        task = AsyncResult(task_id)
        if task.ready():
            context["task_id"] = request.session["task_id"]
            del request.session["task_id"]
        del request.session["recent"]

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

        # This prevents the file from being re-uploaded if the page is refreshed
        request.session["task_id"] = task_id
        request.session["date_added"] = str(datetime.datetime.now())
        request.session["recent"] = True
        return redirect(request.path)

    if "task_id" in request.session and "date_added" in request.session:
        task_id = request.session["task_id"]
        task = AsyncResult(task_id)

        # Get the current time and the time the task was added
        current_time = datetime.datetime.now()
        date_added = datetime.datetime.strptime(
            request.session["date_added"], "%Y-%m-%d %H:%M:%S.%f"
        )
        time_difference = (current_time - date_added).total_seconds()

        # remove the task id if complete or if it got stuck due to an error
        # that occured before Celery picked it up
        if task.ready() or (task.status == "PENDING" and time_difference > 60):
            # If the task is complete, delete the task ID from the session
            del request.session["task_id"]
            del request.session["date_added"]
        else:
            # If the task is not complete, pass the task ID to the context
            context["task_id"] = task_id
            context["date_added"] = request.session["date_added"]

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
            # Define a dictionary mapping form fields to filter conditions
            filters = {
                "sat_name": "satellite_id__sat_name__icontains",
                "sat_number": "satellite_id__sat_number",
                "obs_mode": "obs_mode__icontains",
                "start_date_range": "obs_time_utc__gte",
                "end_date_range": "obs_time_utc__lte",
                "observation_id": "id",
                "observer_orcid": "obs_orc_id__icontains",
                "mpc_code": "mpc_code",
            }

            # Filter observations based on search criteria
            observations = Observation.objects.all()
            for field, condition in filters.items():
                value = form.cleaned_data[field]
                if value:
                    observations = observations.filter(**{condition: value})

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


def about(request):
    template = loader.get_template("repository/about.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


def getting_started(request):
    template = loader.get_template("repository/getting-started.html")
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


def tools(request):
    template = loader.get_template("repository/tools.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


def generate_csv(request):
    if request.method == "POST":
        form = GenerateCSVForm(request.POST)
        if form.is_valid():

            # not the exact same header as the observation download header since this
            # one needs observer_email
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
                "observer_email",
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
            ]

            # for each line in the output field in the form,
            # add the line to a new csv file
            csv_lines = []
            for line in form.cleaned_data["output"].split("\n"):
                reader = csv.reader(io.StringIO(line))
                csv_lines.append(next(reader))

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(csv_lines)

            zipfile_name = "score_upload.zip"
            zipped_file = io.BytesIO()

            with zipfile.ZipFile(zipped_file, "w") as zip:
                zip.writestr("score_upload.csv", output.getvalue())
            zipped_file.seek(0)

            response = HttpResponse(zipped_file, content_type="application/zip")
            response["Content-Disposition"] = f"attachment; filename={zipfile_name}"
            return response

        else:
            return render(request, "repository/generate-csv.html", {"form": form})
    return render(request, "repository/generate-csv.html", {"form": GenerateCSVForm})


def satellite_data_view(request, satellite_number):
    try:
        satellite = Satellite.objects.get(sat_number=satellite_number)
    except Satellite.DoesNotExist:
        context = {
            "error_title": "Satellite Not Found",
            "error_message": "The satellite you're looking for doesn't exist "
            "in our database.",
        }
        return render(request, "404.html", context, status=404)

    observations = satellite.observations.all()
    observation_list_json = [
        (JSONRenderer().render(ObservationSerializer(observation).data))
        for observation in observations
    ]
    observations_and_json = zip(observations, observation_list_json)

    observations_data = [
        {
            "date": observation.obs_time_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "magnitude": observation.apparent_mag,
            "phase_angle": observation.phase_angle,
        }
        for observation in observations
    ]

    # limit the decimal places to 6
    average_magnitude = round(
        observations.aggregate(Avg("apparent_mag"))["apparent_mag__avg"], 6
    )
    first_observation_date = observations.order_by("obs_time_utc").first().obs_time_utc
    most_recent_observation_date = (
        observations.order_by("-obs_time_utc").first().obs_time_utc
    )

    context = {
        "satellite": satellite,
        "observations_and_json": observations_and_json,
        "num_observations": observations.count(),
        "average_magnitude": average_magnitude,
        "first_observation_date": (
            first_observation_date.date() if first_observation_date else None
        ),
        "most_recent_observation_date": (
            most_recent_observation_date.date() if first_observation_date else None
        ),
        "observations_data": observations_data,
    }
    return render(request, "repository/satellites/data_view.html", context)


@csrf_exempt
def name_id_lookup(request):
    """
    This view returns a JSON response containing either the satellite name and NORAD ID
    based on the provided information, or an error message.

    The function expects a POST request with either a NORAD ID or a satellite name.
    If a NORAD ID is provided, the function queries the SatChecker API to get the
    associated satellite name. If a satellite name is provided, the function queries
    the SatChecker API to get the associated NORAD ID.

    If both the NORAD ID and satellite name are provided, or if neither is provided,
    the function returns a JSON response with an appropriate error message.

    If the provided NORAD ID or satellite name is not associated with any satellite,
    the function returns a JSON response with an error message.

    Parameters:
    request (HttpRequest): The Django request object containing either a NORAD ID
    or a satellite name.

    Returns:
    JsonResponse: A JSON response containing either the satellite name and NORAD ID,
    or an error message.
    """
    norad_id = request.POST.get("satellite_id")
    satellite_name = request.POST.get("satellite_name").upper()

    if norad_id and satellite_name:
        return JsonResponse(
            {"error": "Please provide either a NORAD ID or a satellite name."}
        )

    if norad_id:
        satellite_name = get_satellite_name(norad_id)

        if satellite_name is None:
            return JsonResponse(
                {"error": "No satellite found for the provided NORAD ID."}
            )
        return JsonResponse({"satellite_name": satellite_name, "norad_id": norad_id})

    if satellite_name:
        norad_id = get_norad_id(satellite_name)
        if norad_id is None:
            return JsonResponse(
                {"error": "No satellite found for the provided satellite name."}
            )
        return JsonResponse({"satellite_name": satellite_name, "norad_id": norad_id})


@csrf_exempt
def satellite_pos_lookup(request):
    """
    This view returns a JSON response containing the satellite's position and other
    details based on the provided observer's location and time, or an error message.

    The function expects a POST request with the observer's latitude, longitude,
    altitude, and the date and time of observation. It also requires either a NORAD
    ID or a satellite name.

    If a NORAD ID is provided, the function queries the SatChecker API to get the
    associated satellite's position. If a satellite name is provided, the function
    queries the SatChecker API to get the associated satellite's position.

    If the provided NORAD ID or satellite name is not associated with any satellite,
    the function returns a JSON response with an error message.

    Parameters:
    request (HttpRequest): The Django request object containing the observer's
    location, date and time of observation, and either a NORAD ID or a satellite name.

    Returns:
    JsonResponse: A JSON response containing either the satellite's position and other
    details, or an error message.
    """
    observer_latitude = request.POST.get("obs_lat")
    observer_longitude = request.POST.get("obs_long")
    observer_altitude = request.POST.get("obs_alt")
    day = request.POST.get("day")
    month = request.POST.get("month")
    year = request.POST.get("year")
    hour = request.POST.get("hour")
    minutes = request.POST.get("minutes")
    seconds = request.POST.get("seconds")
    norad_id = request.POST.get("satellite_id")
    satellite_name = request.POST.get("satellite_name")

    # Check if any of the values are empty
    if (
        not observer_latitude
        or not observer_longitude
        or not observer_altitude
        or not day
        or not month
        or not year
        or not hour
        or not minutes
        or not seconds
    ):
        return JsonResponse({"error": "One or more required fields are empty."})

    # Convert day, month, year, hour, and minutes to integers
    day = int(day)
    month = int(month)
    year = int(year)
    hour = int(hour)
    minutes = int(minutes)
    seconds = float(seconds)

    if norad_id and satellite_name:
        return JsonResponse(
            {"error": "Please provide either a NORAD ID or a satellite name."}
        )

    # set satellite name to uppercase
    satellite_name = satellite_name.upper()

    # combine date and time to make a julian date with astropy
    # Create a datetime object
    date_time = datetime.datetime(
        year, month, day, hour, minutes, int(seconds), int((seconds % 1) * 1e6)
    )

    # Format the date_time as an ISO 8601 string
    date_time_str = date_time.strftime("%Y-%m-%dT%H:%M:%S.%f")

    julian_date = Time(date_time_str, format="isot", scale="utc").jd

    response = None
    if norad_id:
        url = "https://satchecker.cps.iau.org/ephemeris/catalog-number/"
        params = {
            "catalog": norad_id,
            "latitude": observer_latitude,
            "longitude": observer_longitude,
            "elevation": observer_altitude,
            "julian_date": julian_date,
            "min_altitude": -90,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException:
            return "Satellite position check failed - try again later."
    else:
        url = "https://satchecker.cps.iau.org/ephemeris/name/"
        params = {
            "name": satellite_name,
            "latitude": observer_latitude,
            "longitude": observer_longitude,
            "elevation": observer_altitude,
            "julian_date": julian_date,
            "min_altitude": -90,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException:
            return "Satellite position check failed - try again later."

    if response.status_code != 200 or not response.json():
        return JsonResponse(
            {
                "error": "Satellite position check failed"
                " - check your input and try again."
            }
        )

    response_json = response.json()
    if "data" not in response_json or not response_json["data"]:
        return JsonResponse({"error": "No satellite data found."})

    satellite_data = response_json["data"][0]
    fields = response_json.get("fields", [])

    # Mapping fields to their values for easier access
    data_dict = dict(zip(fields, satellite_data))

    name = data_dict.get("name")
    id = data_dict.get("catalog_id")
    alt = round(data_dict.get("altitude_deg", 0), 6)
    az = round(data_dict.get("azimuth_deg", 0), 6)
    ra = round(data_dict.get("right_ascension_deg", 0), 6)
    dec = round(data_dict.get("declination_deg", 0), 6)
    tle_retrieval_date = data_dict.get("tle_date")

    return JsonResponse(
        {
            "satellite_name": name,
            "norad_id": id,
            "altitude": alt,
            "azimuth": az,
            "ra": ra,
            "dec": dec,
            "tle_date": tle_retrieval_date,
        }
    )


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
