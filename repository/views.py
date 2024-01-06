import datetime
import io
from django.forms import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
import csv

from .models import Satellite, Location, Image, Observation
from .forms import UploadObservationFileForm

def index(request):
    if request.method == "POST" and request.FILES['uploaded_file']:
        form = UploadObservationFileForm(request.POST, request.FILES)
        uploaded_file = request.FILES['uploaded_file']
        filename = uploaded_file.name
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
    paginator = Paginator(observation_list, 10)

    page = request.GET.get('page', 1)
    try:
        observations = paginator.page(page)
    except PageNotAnInteger:
        observations = paginator.page(1)
    except EmptyPage:
        observations = paginator.page(paginator.num_pages)

    return render(request, "repository/view.html",  { 'observations': observations })