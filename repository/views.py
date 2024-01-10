import datetime
import io
import zipfile
from django.forms import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
import csv

from .models import Satellite, Location, Image, Observation
from .forms import UploadObservationFileForm

def index(request):
    if request.method == "POST" and not request.FILES:
        return render(request, "repository/index.html", {"error": "Please select a file to upload."})
    if request.method == "POST" and request.FILES['uploaded_file']:
        uploaded_file = request.FILES['uploaded_file']
        #parse csv file into models
        data_set = uploaded_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        #check if first row is header or not

        next(io_string)  # Skip the header
        obs_ids = []
        try:
            
            for column in csv.reader(io_string, delimiter=',', quotechar="|"):
                satellite, sat_created = Satellite.objects.update_or_create(
                    sat_name = column[0],
                    sat_number = column[1],
                    
                    defaults={
                        'sat_name': column[0],
                        'sat_number': column[1],
                        'date_added': datetime.datetime.now(),
                    },
                )

                location, loc_created = Location.objects.update_or_create(
                    obs_lat_deg = column[6],
                    obs_long_deg =column[7],
                    obs_alt_m = column[8],
                    defaults={
                        'obs_lat_deg': column[6],
                        'obs_long_deg': column[7],
                        'obs_alt_m': column[8],
                        'date_added': datetime.datetime.now(),
                    },
                )

                observation, obs_created = Observation.objects.update_or_create(
                    obs_time_utc = column[2],
                    obs_time_uncert_sec = column[3],
                    apparent_mag = column[4],
                    apparent_mag_uncert = column[5],
                    instrument = column[9],
                    obs_mode = column[10],
                    obs_filter = column[11],
                    obs_email = column[12],
                    obs_orc_id = column[13],
                    sat_ra_deg = column[14],
                    sat_ra_uncert_deg = column[15],
                    sat_dec_deg = column[16],
                    sat_dec_uncert_deg = column[17],
                    range_to_sat_km = column[18],
                    range_to_sat_uncert_km = column[19],
                    range_rate_sat_km_s = column[20],
                    range_rate_sat_uncert_km_s = column[21],
                    comments = column[22],
                    data_archive_link = column[23],
                    satellite_id = satellite,
                    location_id = location,
                    defaults={
                        'obs_time_utc': column[2],
                        'obs_time_uncert_sec': column[3],
                        'apparent_mag': column[4],
                        'apparent_mag_uncert': column[5],
                        'instrument': column[9],
                        'obs_mode': column[10],
                        'obs_filter': column[11],
                        'obs_email': column[12],
                        'obs_orc_id': column[13],
                        'sat_ra_deg': column[14],
                        'sat_ra_uncert_deg': column[15],
                        'sat_dec_deg': column[16],
                        'sat_dec_uncert_deg': column[17],
                        'range_to_sat_km': column[18],
                        'range_to_sat_uncert_km': column[19],
                        'range_rate_sat_km_s': column[20],
                        'range_rate_sat_uncert_km_s': column[21],
                        'comments': column[22],
                        'data_archive_link': column[23],
                        'flag': None,
                        'satellite_id': satellite,
                        'location_id': location,
                        'date_added': datetime.datetime.now(),
                    },
                )
                obs_ids.append(observation.id)

        except ValueError as e:
            return render(request, "repository/index.html", {"error": e})
        except ValidationError as e:
            if len(e.messages) > 1:
                return render(request, "repository/index.html", {"error": e.messages[1]})
            return render(request, "repository/index.html", {"error": e.messages[0]})
        
        return render(request, "repository/index.html", {"obs_id": obs_ids})
    else:
        form = UploadObservationFileForm()
    template = loader.get_template("repository/index.html")
    context = {
        "filename": "",
    }
    return HttpResponse(template.render(context, request))


def data_format(request):
    template = loader.get_template("repository/data-format.html")
    context = {
        "" : ""
    }
    return HttpResponse(template.render(context, request))

def view_data(request):
    observation_list = Observation.objects.all()
    return render(request, "repository/view.html",  { 'observations': observation_list })

def download_all(request):
    #create csv from observation models (All)
    header=["satellite_name", "norad_cat_id", "observation_time_utc", 
            "observation_time_uncertainty_sec", "apparent_magnitude",
            "apparent_magnitude_uncertainty", "observer_latitude_deg",
            "observer_longitude_deg", "observer_altitude_m", "instrument",
            "observing_mode", "observing_filter", "observer_email", "observer_orcid",
            "satellite_right_ascension_deg", "satellite_right_ascension_uncertainty_deg",
            "satellite_declination_deg", "satellite_declination_uncertainty_deg", 
            "range_to_satellite_km", "range_to_satellite_uncertainty_km", 
            "range_rate_of_satellite_km_per_sec", "range_rate_of_satellite_uncertainty_km_per_sec",
            "comments", "data_archive_link"]
    
    observations = Observation.objects.all()

    csv_lines = []
    for observation in observations:
        csv_lines.append([observation.satellite_id.sat_name, observation.satellite_id.sat_number, observation.obs_time_utc, 
            observation.obs_time_uncert_sec, observation.apparent_mag, observation.apparent_mag_uncert, observation.location_id.obs_lat_deg,
            observation.location_id.obs_long_deg, observation.location_id.obs_alt_m, observation.instrument, observation.obs_mode,
            observation.obs_filter, observation.obs_email, observation.obs_orc_id, observation.sat_ra_deg, observation.sat_ra_uncert_deg,
            observation.sat_dec_deg, observation.sat_dec_uncert_deg, observation.range_to_sat_km, observation.range_to_sat_uncert_km,
            observation.range_rate_sat_km_s, observation.range_rate_sat_uncert_km_s, observation.comments, observation.data_archive_link])
        
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(csv_lines)

    zipfile_name = "satellite_observations.zip"
    zipped_file = io.BytesIO()

    with zipfile.ZipFile(zipped_file, 'w') as zip:
        zip.writestr("observations.csv", output.getvalue())
    zipped_file.seek(0)

    response = HttpResponse(zipped_file, content_type="application/zip")
    
    response['Content-Disposition'] = f'attachment; filename={zipfile_name}'
    return response
    