import re

from django import forms
from django.forms import Form

from repository.models import Observation


class UploadObservationFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


def validate_orcid(value):
    orc_id_list = value.split(",")
    for orc_id in orc_id_list:
        if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", orc_id.strip()):
            raise forms.ValidationError("Invalid ORCID.")


def validate_date(value):
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$", value):
        raise forms.ValidationError("Invalid date format.")


class SearchForm(Form):
    sat_name = forms.CharField(
        max_length=200,
        required=False,
        label="Satellite Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    sat_number = forms.IntegerField(
        required=False,
        label="Satellite Number",
        widget=forms.NumberInput(
            attrs={"min": 0, "max": 99999, "class": "form-control"}
        ),
    )

    OBS_MODE_CHOICES_FORM = [("", "Any")] + Observation.OBS_MODE_CHOICES
    obs_mode = forms.ChoiceField(
        choices=OBS_MODE_CHOICES_FORM,
        required=False,
        label="Observation Mode",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    start_date_range = forms.DateField(
        required=False,
        label="Start Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    end_date_range = forms.DateField(
        required=False,
        label="End Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    constellation = forms.CharField(
        max_length=200,
        required=False,
        label="Constellation",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    observation_id = forms.IntegerField(
        required=False,
        label="Observation ID",
        widget=forms.TextInput(attrs={"type": "number", "class": "form-control"}),
    )
    observer_orcid = forms.CharField(
        required=False,
        label="Observer ORCID",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        validators=[validate_orcid],
    )


class SingleObservationForm(Form):
    sat_name = forms.CharField(
        max_length=200,
        required=True,
        label="Satellite Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    sat_number = forms.IntegerField(
        required=True,
        label="Satellite Number",
        widget=forms.NumberInput(
            attrs={"step": 1, "min": 0, "max": 99999, "class": "form-control"}
        ),
    )
    obs_mode = forms.ChoiceField(
        choices=Observation.OBS_MODE_CHOICES,
        required=True,
        label="Observation Mode",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    obs_date = forms.CharField(
        required=True,
        label="Observation Date/Time (UTC)",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Required format: YYYY-MM-DDTHH:MM:SSZ",
        validators=[validate_date],
    )
    obs_date_uncert = forms.FloatField(
        required=True,
        label="Observation Date/Time Uncertainty (sec)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    not_detected = forms.BooleanField(
        required=False,
        label="Not Detected",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    apparent_mag = forms.FloatField(
        required=False,
        label="Apparent Magnitude",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    apparent_mag_uncert = forms.FloatField(
        required=False,
        label="Apparent Magnitude Uncertainty",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    instrument = forms.CharField(
        max_length=200,
        required=True,
        label="Instrument",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    observer_latitude_deg = forms.FloatField(
        required=True,
        label="Observer Latitude (deg)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "min": -90, "max": 90}
        ),
    )
    observer_longitude_deg = forms.FloatField(
        required=True,
        label="Observer Longitude (deg)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "min": -180, "max": 180}
        ),
    )
    observer_altitude_m = forms.FloatField(
        required=True,
        label="Observer Altitude (m)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "min": 0}
        ),
    )
    filter = forms.CharField(
        max_length=200,
        required=True,
        label="Observation Filter",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    observer_email = forms.CharField(
        required=True,
        label="Observer Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    constellation = forms.CharField(
        max_length=200,
        required=False,
        label="Constellation",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    observer_orcid = forms.CharField(
        required=True,
        label="Observer ORCID",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        validators=[validate_orcid],
    )
    sat_ra_deg = forms.FloatField(
        required=False,
        label="Satellite Right Ascension (deg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sat_ra_uncert_deg = forms.FloatField(
        required=False,
        label="Satellite Right Ascension Uncertainty (deg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sat_dec_deg = forms.FloatField(
        required=False,
        label="Satellite Declination (deg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sat_dec_uncert_deg = forms.FloatField(
        required=False,
        label="Satellite Declination Uncertainty (deg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    range_to_sat_km = forms.FloatField(
        required=False,
        label="Range to Satellite (km)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    range_to_sat_uncert_km = forms.FloatField(
        required=False,
        label="Range to Satellite Uncertainty (km)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    range_rate_sat_km_s = forms.FloatField(
        required=False,
        label="Range Rate of Satellite (km/s)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    range_rate_sat_uncert_km_s = forms.FloatField(
        required=False,
        label="Range Rate of Satellite Uncertainty (km/s)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    comments = forms.CharField(
        required=False,
        label="Comments",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    data_archive_link = forms.CharField(
        required=False,
        label="Data Archive Link",
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        # fmt: off
        if not cleaned_data.get("sat_ra_deg") and \
               cleaned_data.get("sat_ra_uncert_deg"):
            errors[
                "sat_ra_uncert_deg"
            ] = "Right ascension uncertainty requires right ascension."
        if not cleaned_data.get("sat_dec_deg") and cleaned_data.get(
            "sat_dec_uncert_deg"
        ):
            errors[
                "sat_dec_uncert_deg"
            ] = "Declination uncertainty requires declination."
        if not cleaned_data.get("range_to_sat_km") and cleaned_data.get(
            "range_to_sat_uncert_km"
        ):
            errors[
                "range_to_sat_uncert_km"
            ] = "Range to satellite uncertainty requires range to satellite."
        if not cleaned_data.get("range_rate_sat_km_s") and cleaned_data.get(
            "range_rate_sat_uncert_km_s"
        ):
            errors[
                "range_rate_sat_uncert_km_s"
            ] = "Range rate uncertainty requires range rate."
        if cleaned_data.get("observer_email") and not re.match(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            cleaned_data.get("observer_email"),
        ):
            errors["observer_email"] = "Observer email is not correctly formatted."
        # fmt: on
        if errors:
            raise forms.ValidationError(errors)
