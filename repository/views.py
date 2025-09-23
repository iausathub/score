import csv
import datetime
import io
import logging
import time
import zipfile
from typing import Union

import requests
from astropy.time import Time
from celery.result import AsyncResult
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from repository.forms import (
    DataChangeForm,
    GenerateCSVForm,
    SearchForm,
)
from repository.models import Observation, Satellite
from repository.serializers import ObservationSerializer
from repository.tasks import process_upload
from repository.utils.csv_utils import create_csv
from repository.utils.email_utils import send_data_change_email
from repository.utils.general_utils import (
    get_norad_id,
    get_satellite_metadata,
    get_satellite_name,
    get_stats,
)
from repository.utils.search_utils import filter_observations

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
        "task_id": None,
        "error": None,
        "recaptcha_public_key": settings.RECAPTCHA_PUBLIC_KEY,
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

    # Ensure task_id is always in context to prevent template errors
    if "task_id" not in context:
        context["task_id"] = None

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
            context["task_id"] = None
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
    observation_list = Observation.objects.order_by("-date_added")[:500].select_related(
        "satellite_id", "location_id"
    )

    return render(
        request,
        "repository/view.html",
        {"observations": observation_list},
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
            return create_and_return_csv(False, None)
        else:
            # If the reCAPTCHA was not valid, return an error message
            return JsonResponse({"error": "Invalid reCAPTCHA. Please try again."})
    # If reCAPTCHA is not enabled (development mode), proceed with the download
    else:
        return create_and_return_csv(False, None)


def api_access(request) -> HttpResponse:
    """
    Render the 'repository/api-access.html' template.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The HttpResponse object with the zipped CSV file.
    """
    template = loader.get_template("repository/api-access.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


def create_and_return_csv(
    observations: Union[list[Observation], bool], prefix: str
) -> HttpResponse:
    """
    Create a CSV file from the provided observations and return it as a zipped file
    in an HTTP response.

    This function generates a CSV file containing the provided observations. If the
    observations parameter is False, the function will include all available
    observations in the CSV file. The CSV file is then zipped and returned as an HTTP
    response with the appropriate headers to prompt a file download.

    Args:
        observations (Union[List[Observation], bool]): A list of Observation objects
            or False. If False, all observations will be included in the CSV file.
        prefix (str): The prefix for the CSV file. This prefix is used to generate the
            filename for the CSV file.

    Returns:
        HttpResponse: An HTTP response containing the zipped CSV file. The Content-Type
        of the response is set to "application/zip", and the Content-Disposition is set
        to make the file a download with the appropriate filename.

    Raises:
        ValueError: If the observations parameter is not a list of Observation objects
            or False.
    """
    zipped_file, zipfile_name = create_csv(observations, prefix)

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
            # Convert form data to a serializable format
            search_params = {}
            for key, value in form.cleaned_data.items():
                if isinstance(value, datetime.date):
                    search_params[key] = value.isoformat()
                else:
                    search_params[key] = value

            request.session["search_params"] = search_params
            observations = filter_observations(form.cleaned_data)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                limit = int(request.POST.get("limit", 25))
                offset = int(request.POST.get("offset", 0))
                sort = request.POST.get("sort", "date_added")
                order = request.POST.get("order", "desc")
                search_term = request.POST.get("search", "")

                # Handle sorting
                if order == "desc":
                    sort = f"-{sort}"
                observations = observations.order_by(sort)

                # Apply search filter if search term exists
                if search_term:
                    observations = observations.filter(
                        Q(satellite_id__sat_name__icontains=search_term)
                        | Q(satellite_id__sat_number__icontains=search_term)
                        | Q(obs_mode__icontains=search_term)
                        | Q(obs_filter__icontains=search_term)
                        | Q(obs_orc_id__icontains=search_term)
                        | Q(instrument__icontains=search_term)
                        | Q(date_added__icontains=search_term)
                        | Q(obs_time_utc__icontains=search_term)
                        | Q(apparent_mag__icontains=search_term)
                        | Q(location_id__obs_lat_deg__icontains=search_term)
                        | Q(location_id__obs_long_deg__icontains=search_term)
                        | Q(location_id__obs_alt_m__icontains=search_term)
                    )

                # Get total count before pagination
                total = observations.count()

                # Return early if no results
                if total == 0:
                    return JsonResponse({"total": 0, "rows": [], "total_results": 0})

                # Paginate
                paginator = Paginator(observations, limit)
                try:
                    page = (offset // limit) + 1
                    page_obj = paginator.page(page)
                except (ValueError, EmptyPage, PageNotAnInteger):
                    page_obj = paginator.page(1)

                # Format data for bootstrap-table
                rows = []
                for obs in page_obj:
                    rows.append(
                        {
                            "date_added": obs.date_added.strftime(
                                "%b. %d, %Y %I:%M %p"
                            ),
                            "date_added_timestamp": obs.date_added.timestamp(),
                            "satellite_name": obs.satellite_id.sat_name,
                            "satellite_number": obs.satellite_id.sat_number,
                            "obs_time_utc": obs.obs_time_utc.strftime(
                                "%b. %d, %Y %I:%M %p"
                            ),
                            "obs_time_utc_timestamp": obs.obs_time_utc.timestamp(),
                            "apparent_mag": obs.apparent_mag,
                            "apparent_mag_uncert": obs.apparent_mag_uncert,
                            "obs_filter": obs.obs_filter,
                            "obs_lat_deg": round(obs.location_id.obs_lat_deg, 4),
                            "obs_long_deg": round(obs.location_id.obs_long_deg, 4),
                            "obs_alt_m": round(obs.location_id.obs_alt_m, 4),
                            "obs_mode": obs.obs_mode,
                            "obs_orc_id": obs.obs_orc_id,
                            "id": obs.id,
                        }
                    )

                return JsonResponse(
                    {
                        "total": total,  # For bootstrap-table pagination
                        "total_results": total,  # For our custom message
                        "rows": rows,
                    }
                )

            # Handle regular form submission
            if len(observations) == 0:
                return render(
                    request,
                    "repository/search.html",
                    {"error": "No observations found.", "form": form},
                )

            # Initial page load
            return render(
                request,
                "repository/search.html",
                {
                    "observations": observations[:25],  # Initial page
                    "obs_ids": [o.id for o in observations],
                    "form": form,
                    "total_results": observations.count(),
                },
            )
        else:
            return render(
                request,
                "repository/search.html",
                {"error": "No observations found.", "form": form},
            )

    return render(request, "repository/search.html", {"form": SearchForm()})


def download_results(request):
    start_time = time.time()
    logger.info("Starting download_results function")

    if request.method == "POST":
        logger.info("POST request received")

        # Benchmark parsing observation IDs
        parse_start = time.time()
        observation_ids = request.POST.get("obs_ids").split(", ")
        observation_ids = [int(i.strip("[]")) for i in observation_ids if i.strip("[]")]
        parse_end = time.time()
        logger.info(
            f"Parsing observation IDs took {parse_end - parse_start:.4f} seconds"
        )

        satellite_name = (
            request.POST.get("satellite_name")
            if request.POST.get("satellite_name")
            else None
        )
        logger.info(f"Satellite name: {satellite_name}")

        # Benchmark database query
        query_start = time.time()
        observations = Observation.objects.filter(id__in=observation_ids)
        query_end = time.time()
        logger.info(f"Database query took {query_end - query_start:.4f} seconds")
        logger.info(f"Number of observations retrieved: {observations.count()}")

        # Benchmark CSV creation and return
        csv_start = time.time()
        response = create_and_return_csv(observations, prefix=satellite_name)
        csv_end = time.time()
        logger.info(f"CSV creation and return took {csv_end - csv_start:.4f} seconds")

        total_time = time.time() - start_time
        logger.info(f"Total download_results execution time: {total_time:.4f} seconds")

        return response

    logger.info("Non-POST request received, returning empty HttpResponse")
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


def policy(request):
    template = loader.get_template("repository/policy.html")
    context = {"": ""}
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
                    "form": DataChangeForm(),
                },
            )
    else:
        form = DataChangeForm()

    return render(request, "repository/data-change.html", {"form": form})


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
    return render(request, "repository/generate-csv.html", {"form": GenerateCSVForm()})


def satellites(request):
    """
    View function to display a list of all satellites.

    This function retrieves/displays all Satellite objects from the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTML page displaying the list of satellites.
    """
    satellites = Satellite.objects.annotate(num_observations=Count("observations"))

    return render(
        request,
        "repository/satellites.html",
        {"satellites": satellites},
    )


def satellite_data_view(request, satellite_number):
    """
    View function to display data for a specific satellite.

    This function retrieves a Satellite object based on the provided satellite number.
    If the satellite or its observations do not exist, it renders a 404 error page.
    Otherwise, it gathers observation data, calculates statistics, and renders them
    in the 'repository/satellites/data_view.html' template.

    Args:
        request (HttpRequest): The HTTP request object.
        satellite_number (int): The unique number identifying the satellite.

    Returns:
        HttpResponse: The rendered HTML page displaying the satellite data or a 404
        error page.
    """
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

    if not observations:
        context = {
            "error_title": "No Observations Found",
            "error_message": "There are no observations for this satellite in "
            "our database.",
        }
        return render(request, "404.html", context, status=404)

    # get satellite metadata from SatChecker
    metadata = get_satellite_metadata(satellite_number)

    observations_data = [
        {
            "date": observation.obs_time_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "magnitude": observation.apparent_mag,
            "phase_angle": observation.phase_angle,
            "magnitude_uncertainty": observation.apparent_mag_uncert,
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
        "observations": observations,
        "num_observations": observations.count(),
        "average_magnitude": average_magnitude,
        "first_observation_date": (
            first_observation_date.date() if first_observation_date else None
        ),
        "most_recent_observation_date": (
            most_recent_observation_date.date() if first_observation_date else None
        ),
        "observations_data": observations_data,
        "rcs_size": metadata.get("rcs_size") if metadata else None,
        "object_type": metadata.get("object_type") if metadata else None,
        "launch_date": metadata.get("launch_date") if metadata else None,
        "decay_date": metadata.get("decay_date") if metadata else None,
        "intl_designator": (
            metadata.get("international_designator") if metadata else None
        ),
        "generation": metadata.get("generation") if metadata else None,
        "obs_ids": [observation.id for observation in observations],
    }

    response = render(request, "repository/satellites/data_view.html", context)
    return response


def launch_view(request, launch_number):
    """
    View function to display data for a specific launch.
    """
    satellites = Satellite.objects.filter(
        intl_designator__icontains=launch_number
    ).annotate(num_observations=Count("observations"))

    return render(
        request,
        "repository/satellites/launch_view.html",
        {
            "satellites": satellites,
            "launch_number": launch_number,
        },
    )


def observer_view(request, orc_id):
    """
    View function to display data for a specific observer.
    """
    observations = Observation.objects.filter(obs_orc_id__icontains=orc_id)
    return render(
        request,
        "repository/observer_view.html",
        {
            "observations": observations,
            "orc_id": orc_id,
        },
    )


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
            response = requests.get(url, params=params, timeout=60)
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
            response = requests.get(url, params=params, timeout=60)
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


@csrf_exempt
def satellite_observations(request, satellite_number):
    """
    Retrieve observations for a specific satellite and return them as JSON.

    Args:
        request (HttpRequest): The request object.
        satellite_number (int): The NORAD ID of the satellite.

    Returns:
        JsonResponse: The JSON response containing the observations for the satellite.
    """

    try:
        satellite = Satellite.objects.get(sat_number=satellite_number)
    except Satellite.DoesNotExist:
        return JsonResponse({"error": "Satellite not found"}, status=404)

    observations = satellite.observations.all()

    # Handle sorting
    sort = request.GET.get("sort")
    order = request.GET.get("order", "desc")

    if sort:
        # Convert table field names to model field names
        field_mapping = {
            "added": "date_added",
            "observed": "obs_time_utc",
            "apparent_mag": "apparent_mag",
            "obs_filter": "obs_filter",
            "obs_mode": "obs_mode",
            "obs_lat_deg": "location_id__obs_lat_deg",
            "obs_long_deg": "location_id__obs_long_deg",
            "obs_alt_m": "location_id__obs_alt_m",
        }

        sort_field = field_mapping.get(sort, sort)
        if order == "desc":
            sort_field = f"-{sort_field}"

        observations = observations.order_by(sort_field)

    limit = int(request.GET.get("limit", 5))
    offset = int(request.GET.get("offset", 0))

    paginator = Paginator(observations, limit)
    page_number = offset // limit + 1
    page_obj = paginator.get_page(page_number)

    observations_data = [
        {
            "date_added": observation.date_added.strftime("%b. %d, %Y %I:%M %p"),
            "added": observation.date_added.timestamp(),
            "sat_name": observation.satellite_id.sat_name,
            "sat_number": observation.satellite_id.sat_number,
            "obs_time_utc": observation.obs_time_utc.strftime("%b. %d, %Y %I:%M %p"),
            "observed": observation.obs_time_utc.timestamp(),
            "apparent_mag": observation.apparent_mag,
            "apparent_mag_uncert": observation.apparent_mag_uncert,
            "obs_filter": observation.obs_filter,
            "obs_lat_deg": round(observation.location_id.obs_lat_deg, 4),
            "obs_long_deg": round(observation.location_id.obs_long_deg, 4),
            "obs_alt_m": round(observation.location_id.obs_alt_m, 4),
            "obs_mode": observation.obs_mode,
            "obs_orc_id": observation.obs_orc_id,
            "observation_id": observation.id,
        }
        for observation in page_obj
    ]

    response_data = {
        "total": paginator.count,
        "rows": observations_data,
        "debug": {
            "limit": limit,
            "offset": offset,
            "page": page_number,
            "total_pages": paginator.num_pages,
            "sort": sort,
            "order": order,
            "sort_field": sort_field if sort else None,
        },
    }
    return JsonResponse(response_data)


@csrf_exempt
def get_observation_by_id(request, observation_id):
    """
    Retrieve observation data by observation ID and return it as JSON.

    Args:
        request (HttpRequest): The request object.
        observation_id (int): The ID of the observation.

    Returns:
        JsonResponse: The JSON response containing the observation data.
    """
    observation = get_object_or_404(Observation, id=observation_id)
    serialized_observation = ObservationSerializer(observation).data
    return JsonResponse(serialized_observation)


@csrf_exempt
def observer_observations(request, orc_id):
    """
    Retrieve observations for a specific observer and return them as JSON.

    Args:
        request (HttpRequest): The request object.
        orc_id (str): The ORCID of the observer.

    Returns:
        JsonResponse: The JSON response containing the observations for the observer.
    """
    observations = Observation.objects.filter(obs_orc_id__icontains=orc_id)

    # Handle sorting
    sort = request.GET.get("sort")
    order = request.GET.get("order", "desc")

    if sort:
        # Convert table field names to model field names
        field_mapping = {
            "satellite_name": "satellite_id__sat_name",
            "satellite_number": "satellite_id__sat_number",
            "observed": "obs_time_utc",
            "apparent_mag": "apparent_mag",
            "obs_filter": "obs_filter",
            "obs_mode": "obs_mode",
            "obs_lat_deg": "location_id__obs_lat_deg",
            "obs_long_deg": "location_id__obs_long_deg",
            "obs_alt_m": "location_id__obs_alt_m",
        }

        sort_field = field_mapping.get(sort, sort)
        if order == "desc":
            sort_field = f"-{sort_field}"

        observations = observations.order_by(sort_field)

    limit = int(request.GET.get("limit", 25))
    offset = int(request.GET.get("offset", 0))

    paginator = Paginator(observations, limit)
    page_number = offset // limit + 1
    page_obj = paginator.get_page(page_number)

    observations_data = [
        {
            "sat_name": observation.satellite_id.sat_name,
            "sat_number": observation.satellite_id.sat_number,
            "obs_time_utc": observation.obs_time_utc.strftime("%b. %d, %Y %I:%M %p"),
            "observed": observation.obs_time_utc.timestamp(),
            "apparent_mag": observation.apparent_mag,
            "apparent_mag_uncert": observation.apparent_mag_uncert,
            "obs_filter": observation.obs_filter,
            "obs_lat_deg": round(observation.location_id.obs_lat_deg, 4),
            "obs_long_deg": round(observation.location_id.obs_long_deg, 4),
            "obs_alt_m": round(observation.location_id.obs_alt_m, 4),
            "obs_mode": observation.obs_mode,
            "observation_id": observation.id,
        }
        for observation in page_obj
    ]

    response_data = {
        "total": paginator.count,
        "rows": observations_data,
        "debug": {
            "limit": limit,
            "offset": offset,
            "page": page_number,
            "total_pages": paginator.num_pages,
            "sort": sort,
            "order": order,
            "sort_field": sort_field if sort else None,
        },
    }
    return JsonResponse(response_data)


@csrf_exempt
def download_observer_data(request):
    """
    Download all observations for a specific observer.

    Args:
        request (HttpRequest): The HTTP request object containing the ORCID.

    Returns:
        HttpResponse: A CSV file containing all observations for the observer.
    """
    logger.info("Starting download_results function")

    if request.method == "POST":
        logger.info("POST request received")

        orc_id = request.POST.get("orc_id") if request.POST.get("orc_id") else None
        logger.info(f"ORCID: {orc_id}")

        observations = Observation.objects.filter(obs_orc_id__icontains=orc_id)
        logger.info(f"Number of observations retrieved: {observations.count()}")

        response = create_and_return_csv(observations, prefix=orc_id)
        return response

    logger.info("Non-POST request received, returning empty HttpResponse")
    return HttpResponse()
