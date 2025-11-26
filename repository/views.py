import csv
import datetime
import io
import logging
import re
import time
import uuid
import zipfile
from datetime import timedelta

import requests
from astropy.time import Time
from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Count, Max, Min, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

from repository.forms import (
    DataChangeForm,
    GenerateCSVForm,
    SearchForm,
)
from repository.models import APIKey, APIKeyVerification, Observation, Satellite
from repository.serializers import ObservationSerializer
from repository.tasks import process_upload_csv
from repository.utils.csv_utils import create_csv
from repository.utils.email_utils import (
    send_api_key_verification_email,
    send_data_change_email,
)
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
        upload_task = process_upload_csv.delay(obs)
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
    Render the 'repository/api_access.html' template.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The HttpResponse object with the zipped CSV file.
    """
    template = loader.get_template("repository/api_access.html")
    context = {"": ""}
    return HttpResponse(template.render(context, request))


@ratelimit(key="ip", rate="3/h", method="POST")
@ratelimit(key="post:email", rate="3/h", method="POST")
def request_api_key(request) -> HttpResponse:
    """
    Render the 'repository/request_api_key.html' template.
    Rate limited to 3 requests per hour per IP and per email.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The HttpResponse object with the rendered template.
    """

    # verify ORCID ID - if invalid, update the form field with an error message
    # sanitize content of ORCID field and check for correct format (last character
    # can be a letter)
    # then try the orcid at https://orcid.org/{orcid_id}
    # see if the page exists - if not, update the form field with an error message

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        orcid_id = request.POST.get("orcid_id")

        # Validation
        if not name or not email:
            messages.error(request, "Invalid request. Please try again.")
            return render(request, "repository/admin/create_api_key.html")

        try:
            orcid_error_message = "Invalid ORCID ID. Must be a valid ORCID ID."
            # Validate and sanitize the ORCID ID
            orcid_id = orcid_id.strip().upper()
            if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]$", orcid_id):
                messages.error(request, orcid_error_message)
                return render(request, "repository/request_api_key.html")

            # Use Accept header to get XML response, which returns 404 for invalid
            # ORCID IDs - if using the regular request it returns 200 for everything.
            response = requests.get(
                f"https://orcid.org/{orcid_id}",
                headers={"Accept": "application/xml"},
                timeout=30,
            )
            if response.status_code != 200:
                messages.error(request, orcid_error_message)
                return render(request, "repository/request_api_key.html")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            return render(request, "repository/request_api_key.html")

        # Send verification email to the email address provided
        verification_token = uuid.uuid4()
        APIKeyVerification.objects.create(
            name=name,
            email=email,
            orcid_id=orcid_id,
            verification_token=verification_token,
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        send_api_key_verification_email(email, verification_token)
        messages.success(request, "Verification email sent. Please check your email.")

    return render(request, "repository/request_api_key.html")


@ratelimit(key="ip", rate="10/h", method="GET")
def verify_email(request, token):
    """
    Verify the email address and create the API key.
    Token is single-use and expires in 30 minutes.
    Rate limited to 10 verification attempts per hour per IP.
    """
    try:
        verification = APIKeyVerification.objects.get(verification_token=token)

        if not verification.is_active():
            return render(request, "repository/verification_failed.html")

        # Create the API key
        api_key, plaintext_key = APIKey.create_key(
            name=verification.name,
            email=verification.email,
            orcid_id=verification.orcid_id,
            expires_in_days=90,
        )

        # Delete verification record (single-use token)
        verification.delete()

        # Store the plaintext key in session to display on next page
        request.session["new_api_key"] = {
            "key": plaintext_key,
            "name": api_key.name,
            "email": api_key.email,
            "prefix": api_key.key_prefix,
            "created_at": api_key.created_at.isoformat(),
            "expires_at": (
                api_key.expires_at.isoformat() if api_key.expires_at else None
            ),
        }
        # Set session to expire when browser closes for security
        request.session.set_expiry(0)

        # Prevent token leakage via Referer header
        response = redirect("show_api_key")
        response["Referrer-Policy"] = "no-referrer"
        return response

    except APIKeyVerification.DoesNotExist:
        return render(request, "repository/verification_failed.html")
    except Exception as e:
        logger.error(f"Error during email verification: {e}", exc_info=True)
        messages.error(
            request, "An error occurred during verification. Please try again."
        )
        return redirect("request-api-key")


def show_api_key_view(request):
    """
    Display the newly created API key.
    This is the only time the plaintext key will be shown.
    Accessible to staff members OR users with valid session from email verification.
    """

    # Get the key from session (pops it out for security)
    api_key_data = request.session.pop("new_api_key", None)

    # Security check: Must have session data OR be staff
    if not api_key_data:
        if request.user.is_authenticated and request.user.is_staff:
            messages.warning(request, "No API key to display. Create a new one.")
            return redirect("create_api_key")
        else:
            # For non-staff users, redirect to API access page
            messages.warning(
                request, "API key link has expired or already been viewed."
            )
            return redirect("api-access")

    # Convert ISO format strings back to datetime objects for template
    if api_key_data.get("created_at"):
        api_key_data["created_at"] = datetime.datetime.fromisoformat(
            api_key_data["created_at"]
        )
    if api_key_data.get("expires_at"):
        api_key_data["expires_at"] = datetime.datetime.fromisoformat(
            api_key_data["expires_at"]
        )

    return render(request, "repository/show_api_key.html", {"api_key": api_key_data})


def create_and_return_csv(
    observations: list[Observation] | bool, prefix: str
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

                # Get all observation IDs for download
                if isinstance(observations, list):
                    all_obs_ids = [o.id for o in observations]
                else:
                    all_obs_ids = list(observations.values_list("id", flat=True))

                # Return early if no results
                if total == 0:
                    return JsonResponse(
                        {"total": 0, "rows": [], "total_results": 0, "obs_ids": []}
                    )

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
                        "obs_ids": all_obs_ids,  # For download button
                    }
                )

            # Handle regular form submission
            # Check if observations is a list (from location filtering) or QuerySet
            if isinstance(observations, list):
                obs_count = len(observations)
                obs_ids_list = [o.id for o in observations]
            else:
                obs_count = observations.count()
                obs_ids_list = list(observations.values_list("id", flat=True))

            if obs_count == 0:
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
                    "observations": observations[:25],
                    "obs_ids": obs_ids_list,
                    "form": form,
                    "total_results": obs_count,
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

        # Parse observation IDs from POST data
        parse_start = time.time()
        obs_ids_str = request.POST.get("obs_ids", "")
        if obs_ids_str:
            observation_ids = obs_ids_str.split(", ")
            observation_ids = [
                int(i.strip("[]")) for i in observation_ids if i.strip("[]")
            ]
        else:
            observation_ids = []
        parse_end = time.time()
        logger.info(
            f"Parsing observation IDs took {parse_end - parse_start:.4f} seconds"
        )
        logger.info(f"Using {len(observation_ids)} observation IDs for download")

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
            "sat_altitude_km_satchecker": observation.sat_altitude_km_satchecker,
            "solar_elevation_deg_satchecker": (
                observation.solar_elevation_deg_satchecker
            ),
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


def _get_constellation_id(sat_name):
    """Helper to determine constellation from satellite name."""
    sat_name_upper = (sat_name or "").upper()
    if "STARLINK" in sat_name_upper:
        return "starlink"
    elif "KUIPER" in sat_name_upper:
        return "kuiper"
    elif "QIANFAN" in sat_name_upper:
        return "qianfan"
    elif "SPACEMOBILE" in sat_name_upper:
        return "spacemobile"
    elif "ONEWEB" in sat_name_upper:
        return "oneweb"
    return "other"


def _get_constellation_filter(const_id):
    """Helper to get Q filter for constellation."""
    if const_id == "starlink":
        return Q(satellite_id__sat_name__icontains="STARLINK")
    elif const_id == "kuiper":
        return Q(satellite_id__sat_name__icontains="KUIPER")
    elif const_id == "qianfan":
        return Q(satellite_id__sat_name__icontains="QIANFAN")
    elif const_id == "spacemobile":
        return Q(satellite_id__sat_name__icontains="SPACEMOBILE")
    elif const_id == "oneweb":
        return Q(satellite_id__sat_name__icontains="ONEWEB")
    else:  # other
        return (
            ~Q(satellite_id__sat_name__icontains="STARLINK")
            & ~Q(satellite_id__sat_name__icontains="KUIPER")
            & ~Q(satellite_id__sat_name__icontains="QIANFAN")
            & ~Q(satellite_id__sat_name__icontains="SPACEMOBILE")
            & ~Q(satellite_id__sat_name__icontains="ONEWEB")
        )


def visualization_view(request):
    """Landing page with constellation stats and magnitude histogram."""
    # Constellation definitions
    constellations_config = {
        "starlink": {"name": "Starlink"},
        "kuiper": {"name": "Kuiper"},
        "qianfan": {"name": "Qianfan"},
        "spacemobile": {"name": "AST SpaceMobile"},
        "oneweb": {"name": "OneWeb"},
        # 'other': {'name': 'Other'},
    }

    # Get actual magnitude range from data
    mag_stats = Observation.objects.aggregate(
        min_mag=Min("apparent_mag"), max_mag=Max("apparent_mag")
    )
    min_mag = int(mag_stats["min_mag"]) if mag_stats["min_mag"] else 0
    max_mag = int(mag_stats["max_mag"]) + 1 if mag_stats["max_mag"] else 12

    # Calculate stats for each constellation using database queries
    constellation_stats = []
    magnitude_bins = {i: {} for i in range(min_mag, max_mag + 1)}

    for const_id, const_info in constellations_config.items():
        filter_q = _get_constellation_filter(const_id)

        # Get stats for this constellation
        obs_qs = Observation.objects.filter(filter_q)
        obs_count = obs_qs.count()
        sat_count = Satellite.objects.filter(observations__in=obs_qs).distinct().count()
        avg_mag = obs_qs.aggregate(Avg("apparent_mag"))["apparent_mag__avg"]

        constellation_stats.append(
            {
                "id": const_id,
                "name": const_info["name"],
                "satellite_count": sat_count,
                "observation_count": obs_count,
                "avg_magnitude": round(avg_mag, 2) if avg_mag else None,
            }
        )

        # Get magnitude distribution using database aggregation
        for mag_bin in range(min_mag, max_mag + 1):
            count = obs_qs.filter(
                apparent_mag__gte=mag_bin, apparent_mag__lt=mag_bin + 1
            ).count()
            magnitude_bins[mag_bin][const_id] = count

    # Sort by observation count, but keep "Other" at the end
    constellation_stats.sort(key=lambda x: (-x["observation_count"]))

    # Get all observations for the all-sky plot
    # Only fetch minimal fields since tooltips are disabled
    observations = [
        {
            "alt_deg_satchecker": obs["alt_deg_satchecker"],
            "az_deg_satchecker": obs["az_deg_satchecker"],
            "magnitude": obs["apparent_mag"],
        }
        for obs in Observation.objects.filter(
            alt_deg_satchecker__isnull=False,
            az_deg_satchecker__isnull=False,
            apparent_mag__isnull=False,
        ).values("alt_deg_satchecker", "az_deg_satchecker", "apparent_mag")
        # Uncomment to limit for performance: [:10000]
    ]

    return render(
        request,
        "repository/data_visualization.html",
        {
            "constellation_stats": constellation_stats,
            "magnitude_bins": magnitude_bins,
            "observations": observations,
        },
    )


def graphs_view(request):
    """
    View function to display data for the graphs page.
    """

    return render(
        request,
        "repository/visualization/graphs.html",
        {
            "": "",
        },
    )


def plots_view(request):
    """
    View function to display data for the plots page.
    """

    return render(
        request,
        "repository/visualization/plots.html",
        {
            "": "",
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
    data_dict = dict(zip(fields, satellite_data, strict=True))

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


@csrf_exempt
def get_satellite_data(request):
    """
    Endpoint to get satellite data for the visualizations page
    """
    try:
        satellites_with_observations = (
            Satellite.objects.filter(observations__isnull=False)
            .distinct()
            .select_related()
        )

        constellations = {}

        for satellite in satellites_with_observations:
            sat_name = satellite.sat_name or ""

            # Determine constellation based on satellite name patterns
            constellation_id = "other"

            if "STARLINK" in sat_name.upper() or "STARLINK" in str(
                satellite.sat_number
            ):
                constellation_id = "starlink"
            elif "KUIPER" in sat_name.upper() or "KUIPER" in str(satellite.sat_number):
                constellation_id = "kuiper"
            elif "QIANFAN" in sat_name.upper():
                constellation_id = "qianfan"
            elif "SPACEMOBILE" in sat_name.upper():
                constellation_id = "spacemobile"
            elif "ONEWEB" in sat_name.upper():
                constellation_id = "oneweb"

            if constellation_id not in constellations:
                constellations[constellation_id] = {"count": 0, "satellites": []}

            constellations[constellation_id]["satellites"].append(sat_name)
            constellations[constellation_id]["count"] += 1

        # Format expected by satellite_selector.js
        result = {}
        for const_id, data in constellations.items():
            result[const_id] = {
                "count": data["count"],
                "satellites": data["satellites"][:100],  # limited for performance
                "total_available": data["count"],
            }

        return JsonResponse({"success": True, "constellations": result})

    except Exception:
        logger.exception("Error getting satellite data")
        return JsonResponse(
            {"success": False, "error": "Error getting satellite data."},
            status=500,
        )


@csrf_exempt
def get_observations_for_satellites(request):
    """
    API endpoint to get observations for selected satellites
    """
    from django.db.models import Q

    try:
        # Get selected satellites from request
        selected_satellites = request.GET.getlist("satellites[]")
        selected_constellations = request.GET.getlist("constellations[]")

        # Build query for observations
        observations_query = Observation.objects.select_related(
            "satellite_id", "location_id"
        )

        # Build combined filter using Q objects for OR logic
        combined_filters = Q()

        # Add individual satellite filters
        if selected_satellites:
            combined_filters |= Q(satellite_id__sat_name__in=selected_satellites)

        # Add constellation filters
        if selected_constellations:
            for constellation in selected_constellations:
                if constellation == "starlink":
                    combined_filters |= Q(satellite_id__sat_name__icontains="STARLINK")
                elif constellation == "kuiper":
                    combined_filters |= Q(satellite_id__sat_name__icontains="KUIPER")
                elif constellation == "qianfan":
                    combined_filters |= Q(satellite_id__sat_name__icontains="QIANFAN")
                elif constellation == "spacemobile":
                    combined_filters |= Q(
                        satellite_id__sat_name__icontains="SPACEMOBILE"
                    )
                elif constellation == "oneweb":
                    combined_filters |= Q(satellite_id__sat_name__icontains="ONEWEB")
                elif constellation == "other":
                    # "Other" means anything that's NOT the known constellations
                    combined_filters |= (
                        ~Q(satellite_id__sat_name__icontains="STARLINK")
                        & ~Q(satellite_id__sat_name__icontains="KUIPER")
                        & ~Q(satellite_id__sat_name__icontains="QIANFAN")
                        & ~Q(satellite_id__sat_name__icontains="SPACEMOBILE")
                        & ~Q(satellite_id__sat_name__icontains="ONEWEB")
                    )

        # Apply the combined filter only if satellites/constellations are selected
        if combined_filters:
            observations_query = observations_query.filter(combined_filters)

        # Apply additional filters
        # Date range filters (UTC only)
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        if start_date:
            # Filter by date (inclusive, start of day UTC)
            observations_query = observations_query.filter(
                obs_time_utc__date__gte=start_date
            )
        if end_date:
            # Filter by date (inclusive, entire day UTC)
            observations_query = observations_query.filter(
                obs_time_utc__date__lte=end_date
            )

        # Magnitude filters
        min_mag = request.GET.get("min_mag")
        max_mag = request.GET.get("max_mag")
        if min_mag:
            observations_query = observations_query.filter(
                apparent_mag__gte=float(min_mag)
            )
        if max_mag:
            observations_query = observations_query.filter(
                apparent_mag__lte=float(max_mag)
            )

        # Satellite elevation filters (altitude in km)
        min_sat_elev = request.GET.get("min_sat_elev")
        max_sat_elev = request.GET.get("max_sat_elev")
        if min_sat_elev:
            observations_query = observations_query.filter(
                sat_altitude_km_satchecker__gte=float(min_sat_elev)
            )
        if max_sat_elev:
            observations_query = observations_query.filter(
                sat_altitude_km_satchecker__lte=float(max_sat_elev)
            )

        # Solar elevation filters
        min_solar_elev = request.GET.get("min_solar_elev")
        max_solar_elev = request.GET.get("max_solar_elev")
        if min_solar_elev:
            observations_query = observations_query.filter(
                solar_elevation_deg_satchecker__gte=float(min_solar_elev)
            )
        if max_solar_elev:
            observations_query = observations_query.filter(
                solar_elevation_deg_satchecker__lte=float(max_solar_elev)
            )

        # Get observations data
        observations = observations_query.values(
            "obs_time_utc",
            "apparent_mag",
            "apparent_mag_uncert",
            "sat_ra_deg",
            "sat_dec_deg",
            "phase_angle",
            "sat_altitude_km_satchecker",
            "solar_elevation_deg_satchecker",
            "alt_deg_satchecker",
            "az_deg_satchecker",
            "satellite_id__sat_name",
            "location_id__obs_lat_deg",
            "location_id__obs_long_deg",
            "location_id__obs_alt_m",
        ).order_by("obs_time_utc")

        # Convert to format expected by charts
        chart_data = []
        for obs in observations:
            sat_name = obs["satellite_id__sat_name"] or ""

            # Determine constellation ID for color mapping
            constellation_id = "other"
            if "STARLINK" in sat_name.upper():
                constellation_id = "starlink"
            elif "KUIPER" in sat_name.upper():
                constellation_id = "kuiper"
            elif "QIANFAN" in sat_name.upper():
                constellation_id = "qianfan"
            elif "SPACEMOBILE" in sat_name.upper():
                constellation_id = "spacemobile"
            elif "ONEWEB" in sat_name.upper():
                constellation_id = "oneweb"

            chart_data.append(
                {
                    "date": obs["obs_time_utc"].isoformat(),
                    "magnitude": obs["apparent_mag"],
                    "magnitude_uncertainty": obs["apparent_mag_uncert"],
                    "phase_angle": obs["phase_angle"],
                    "sat_altitude_km_satchecker": obs["sat_altitude_km_satchecker"],
                    "solar_elevation_deg_satchecker": (
                        obs["solar_elevation_deg_satchecker"]
                    ),
                    "alt_deg_satchecker": obs["alt_deg_satchecker"],
                    "az_deg_satchecker": obs["az_deg_satchecker"],
                    "satellite": sat_name,
                    "constellation": constellation_id,
                    "location": (
                        f"{obs['location_id__obs_lat_deg']:.3f}, "
                        f"{obs['location_id__obs_long_deg']:.3f}"
                    ),
                    "ra": obs["sat_ra_deg"],
                    "dec": obs["sat_dec_deg"],
                    "lat": obs["location_id__obs_lat_deg"],
                    "lon": obs["location_id__obs_long_deg"],
                    "alt": obs["location_id__obs_alt_m"],
                }
            )

        return JsonResponse(
            {"success": True, "observations": chart_data, "count": len(chart_data)}
        )

    except Exception:
        logger.exception("Error getting observations for satellites")
        return JsonResponse(
            {"success": False, "error": "Error getting observations for satellites."},
            status=500,
        )
