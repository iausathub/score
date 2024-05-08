import re

from django import forms
from django.core.validators import validate_email
from django.forms import Form, ValidationError

from repository.models import Observation


class UploadObservationFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


def validate_orcid(value: str) -> None:
    """
    Validates the provided ORCID.

    This function checks if the provided ORCID is valid by splitting the input string
    into a list of ORCIDs, and then checking each ORCID against a regular expression.
    If any ORCID does not match the regular expression, a ValidationError is raised.

    Args:
        value (AnyStr): A string containing one or more ORCIDs, separated by commas.

    Raises:
        forms.ValidationError: If any ORCID in the input string is not valid.
    """
    orc_id_list = value.split(",")
    for orc_id in orc_id_list:
        if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", orc_id.strip()):
            raise forms.ValidationError("Invalid ORCID.")


def validate_date(value: str) -> None:
    """
    Validates the provided date string.

    This function checks if the provided date string is in the correct format by
    matching it against a regular expression. The expected format is
    'YYYY-MM-DDTHH:MM:SS(.SSS)Z'. If the date string does not match this format,
    a ValidationError is raised.

    Args:
        value (AnyStr): A string containing the date to be validated.

    Raises:
        forms.ValidationError: If the date string is not in the expected format.
    """
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
            attrs={"min": 0, "max": 99999, "class": "form-control no-arrows"}
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
    observation_id = forms.IntegerField(
        required=False,
        label="Observation ID",
        widget=forms.TextInput(
            attrs={"type": "number", "class": "form-control no-arrows"}
        ),
    )
    observer_orcid = forms.CharField(
        required=False,
        label="Observer ORCID",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        validators=[validate_orcid],
    )
    mpc_code = forms.CharField(
        required=False,
        label="MPC Observatory Code",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )


class SingleObservationForm(Form):
    sat_name = forms.CharField(
        max_length=200,
        required=False,
        label="Satellite Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    sat_number = forms.IntegerField(
        required=True,
        label="Satellite Number",
        widget=forms.NumberInput(
            attrs={"min": 0, "max": 99999, "class": "form-control no-arrows"}
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
    limiting_magnitude = forms.FloatField(
        required=True,
        label="Limiting Magnitude",
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
            attrs={
                "id": "observer_latitude_deg",
                "class": "form-control",
                "step": "any",
                "min": -90,
                "max": 90,
            }
        ),
    )
    observer_longitude_deg = forms.FloatField(
        required=True,
        label="Observer Longitude (deg)",
        widget=forms.NumberInput(
            attrs={
                "id": "observer_longitude_deg",
                "class": "form-control",
                "step": "any",
                "min": -180,
                "max": 180,
            }
        ),
    )
    observer_altitude_m = forms.FloatField(
        required=True,
        label="Observer Altitude (m)",
        widget=forms.NumberInput(
            attrs={
                "id": "observer_altitude_m",
                "class": "form-control",
                "step": "any",
                "min": 0,
            }
        ),
    )
    filter = forms.CharField(
        max_length=200,
        required=True,
        label="Observation Filter",
        help_text="Use 'CLEAR' if observing mode is visual",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    observer_email = forms.CharField(
        required=True,
        label="Observer Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    observer_orcid = forms.CharField(
        required=True,
        label="Observer ORCID",
        widget=forms.TextInput(attrs={"id": "observer_orcid", "class": "form-control"}),
        validators=[validate_orcid],
    )
    sat_ra_deg = forms.FloatField(
        required=False,
        label="Satellite Right Ascension (deg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sat_dec_deg = forms.FloatField(
        required=False,
        label="Satellite Declination (deg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sigma_2_ra = forms.FloatField(
        required=False,
        label="Sigma^2 - RA (deg)",
        help_text="Uncertainty in RA^2",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sigma_ra_sigma_dec = forms.FloatField(
        required=False,
        label="Sigma RA * Sigma Dec (deg)",
        help_text="Uncertainty in RA * Uncertainty in Dec",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )
    sigma_2_dec = forms.FloatField(
        required=False,
        label="Sigma^2 - Dec (deg)",
        help_text="Uncertainty in Dec^2",
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
    mpc_code = forms.CharField(
        required=False,
        label="MPC Observatory Code",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        # fmt: off
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
        if (
            cleaned_data.get("apparent_mag_uncert")
            and not cleaned_data.get("apparent_mag")
            and not cleaned_data.get("not_detected")
        ):
            errors["apparent_mag"] = (
                "Apparent magnitude is required if "
                "apparent magnitude uncertainty is provided."
            )
        # fmt: on
        if errors:
            raise forms.ValidationError(errors)


class DataChangeForm(Form):
    contact_email = forms.EmailField(
        required=True,
        label="Contact email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    obs_ids = forms.CharField(
        required=True,
        label="Observation IDs",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    reason = forms.CharField(
        required=True,
        label="Reason for data change/deletion",
        widget=forms.Textarea(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        email = cleaned_data.get("contact_email")

        try:
            validate_email(email)
        except ValidationError:
            errors["contact_email"] = "Enter a valid email address."

        if errors:
            raise forms.ValidationError(errors)
