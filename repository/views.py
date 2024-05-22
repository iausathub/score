import csv
import datetime
import io
import logging
import zipfile
from typing import Union

import requests
from celery.result import AsyncResult
from django.conf import settings
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
    get_stats,
    send_data_change_email,
)

from .models import Observation
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


@csrf_exempt
def name_id_lookup(request):
    """
    This view returns the satellite name or NORAD ID based on the provided information.

    The NORAD ID or satellite name is received from a POST request. If only the NORAD ID
    is provided, the function queries the SatChecker API to get the associated satellite
    name. If only the satellite name is provided, the function queries the SatChecker
    API to get the associated NORAD ID.

    If both the NORAD ID and satellite name are provided, the function returns a JSON
    response with an error message. If neither is provided, the function does nothing
    and returns None.

    If the NORAD ID or satellite name is not valid/complete or there is no satellite
    associated with it, the function returns a JSON response with an error message.

    Parameters:
    request (HttpRequest): The Django request object.

    Returns:
    JsonResponse: A JSON response with the satellite name and NORAD ID or an error
    message.
    """
    norad_id = request.POST.get("satellite_id")
    satellite_name = request.POST.get("satellite_name").upper()
    error = None

    if norad_id and satellite_name:
        print("Both norad_id and satellite_name provided")
        return JsonResponse(
            {
                "error": "Please provide either a NORAD ID or a satellite name.",
            }
        )

    if norad_id:
        # query SatChecker for satellite name
        url = "https://cps.iau.org/tools/satchecker/api/tools/names-from-norad-id/"
        params = {
            "id": norad_id,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                error = "Satellite info check failed - check the input and try again."
            if not response.json() or response.json()[0] == []:
                error = "No satellite found for the provided NORAD ID."
            else:
                satellite_name = response.json()[0]["name"]
        except requests.exceptions.RequestException:
            error = "Satellite info check failed - try again later."

    elif satellite_name:
        # query SatChecker for NORAD ID
        url = "https://cps.iau.org/tools/satchecker/api/tools/norad-ids-from-name/"
        params = {
            "name": satellite_name,
        }
        try:
            print(url)
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                error = "Satellite info check failed - check the input and try again."
                error += " Status code: " + str(response.status_code)
            if not response.json():
                error = "No satellite found for the provided satellite name."
            else:
                norad_id = response.json()[0]["norad_id"]
        except requests.exceptions.RequestException:
            error = "Satellite info check failed - try again later."

    if not error:
        return JsonResponse(
            {
                "satellite_name": satellite_name,
                "norad_id": norad_id,
            }
        )

    return JsonResponse(
        {
            "error": error,
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
