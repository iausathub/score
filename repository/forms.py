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
            attrs={"min": 0, "max": 999999, "class": "form-control no-arrows"}
        ),
    )
    intl_designator = forms.CharField(
        max_length=200,
        required=False,
        label="International Designator/COSPAR ID",
        widget=forms.TextInput(attrs={"class": "form-control"}),
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
    has_position_data = forms.BooleanField(
        required=False,
        label="Only show observations with position data",
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    instrument = forms.CharField(
        required=False,
        label="Instrument",
        widget=forms.TextInput(attrs={"class": "form-control"}),
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

    observer_latitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control no-arrows", "placeholder": "Latitude"}
        ),
    )
    observer_longitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control no-arrows", "placeholder": "Longitude"}
        ),
    )
    observer_radius = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control no-arrows", "placeholder": "Search Radius"}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("observer_latitude")
        longitude = cleaned_data.get("observer_longitude")
        radius = cleaned_data.get("observer_radius")

        if any([latitude, longitude, radius]):
            if not all([latitude, longitude, radius]):
                raise forms.ValidationError(
                    "If any of latitude, longitude, or radius "
                    "is provided, all three must be specified for observer location."
                )

        return cleaned_data


class GenerateCSVForm(Form):
    sat_name = forms.CharField(
        max_length=200,
        required=False,
        label="Satellite Name",
        widget=forms.TextInput(attrs={"class": "form-control", "id": "sat_name"}),
    )
    sat_number = forms.IntegerField(
        required=False,
        label="Satellite Number",
        widget=forms.NumberInput(
            attrs={
                "min": 0,
                "max": 999999,
                "class": "form-control no-arrows",
                "id": "sat_number",
            }
        ),
    )
    obs_mode = forms.ChoiceField(
        choices=Observation.OBS_MODE_CHOICES,
        required=False,
        label="Observation Mode",
        widget=forms.Select(attrs={"class": "form-select", "id": "obs_mode"}),
    )
    obs_date_year = forms.IntegerField(
        required=False,
        label="YYYY",
        widget=forms.NumberInput(
            attrs={
                "min": 0,
                "max": 99999,
                "class": "form-control no-arrows",
                "id": "obs_date_year",
            }
        ),
    )
    obs_date_month = forms.IntegerField(
        required=False,
        label="MM",
        widget=forms.NumberInput(
            attrs={
                "min": 1,
                "max": 12,
                "class": "form-control no-arrows",
                "id": "obs_date_month",
            }
        ),
    )
    obs_date_day = forms.IntegerField(
        required=False,
        label="DD",
        widget=forms.NumberInput(
            attrs={
                "min": 1,
                "max": 31,
                "class": "form-control no-arrows",
                "id": "obs_date_day",
            }
        ),
    )
    obs_date_hour = forms.IntegerField(
        required=False,
        label="HH",
        widget=forms.NumberInput(
            attrs={
                "min": 0,
                "max": 24,
                "class": "form-control no-arrows",
                "id": "obs_date_hour",
            }
        ),
    )
    obs_date_min = forms.IntegerField(
        required=False,
        label="MM",
        widget=forms.NumberInput(
            attrs={
                "min": 0,
                "max": 60,
                "class": "form-control no-arrows",
                "id": "obs_date_min",
            }
        ),
    )
    obs_date_sec = forms.DecimalField(
        required=False,
        label="SS.ssssss",
        widget=forms.NumberInput(
            attrs={
                "min": 0,
                "max": 60,
                "class": "form-control no-arrows",
                "id": "obs_date_sec",
            }
        ),
    )

    obs_date_uncert = forms.FloatField(
        required=False,
        label="Uncertainty (sec)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "obs_date_uncert"}
        ),
    )
    not_detected = forms.BooleanField(
        required=False,
        label="Not detected/seen",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "not_detected"}
        ),
    )
    apparent_mag = forms.FloatField(
        required=False,
        label="Apparent Magnitude",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "apparent_mag"}
        ),
    )
    apparent_mag_uncert = forms.FloatField(
        required=False,
        label="Apparent Magnitude Uncertainty",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "apparent_mag_uncert"}
        ),
    )
    limiting_magnitude = forms.FloatField(
        required=False,
        label="Limiting Magnitude",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "limiting_magnitude"}
        ),
    )
    instrument = forms.CharField(
        max_length=200,
        required=False,
        label="Instrument",
        widget=forms.TextInput(attrs={"class": "form-control", "id": "instrument"}),
    )
    observer_latitude_deg = forms.FloatField(
        required=False,
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
        required=False,
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
        required=False,
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
        required=False,
        label="Observation Filter",
        help_text="Use 'CLEAR' if observing mode is visual",
        widget=forms.TextInput(attrs={"class": "form-control", "id": "filter"}),
    )
    observer_email = forms.CharField(
        required=False,
        label="Observer Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "id": "observer_email"}
        ),
    )
    observer_orcid = forms.CharField(
        required=False,
        label="Observer ORCID",
        widget=forms.TextInput(attrs={"id": "observer_orcid", "class": "form-control"}),
        validators=[validate_orcid],
    )
    sat_ra_deg = forms.FloatField(
        required=False,
        label="Satellite Right Ascension (deg)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "sat_ra_deg"}
        ),
    )
    sat_dec_deg = forms.FloatField(
        required=False,
        label="Satellite Declination (deg)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "sat_dec_deg"}
        ),
    )
    sigma_2_ra = forms.FloatField(
        required=False,
        label="σ² RA (arcsec²)",
        help_text="Variance of RA",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "sigma_2_ra"}
        ),
    )
    sigma_ra_sigma_dec = forms.FloatField(
        required=False,
        label="σ RA * σ Dec (arcsec²)",
        help_text="Covariance of RA and Dec",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "sigma_ra_sigma_dec"}
        ),
    )
    sigma_2_dec = forms.FloatField(
        required=False,
        label="σ² Dec (arcsec²)",
        help_text="Variance of Dec",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "sigma_2_dec"}
        ),
    )
    range_to_sat_km = forms.FloatField(
        required=False,
        label="Range to Satellite (km)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "range_to_sat_km"}
        ),
    )
    range_to_sat_uncert_km = forms.FloatField(
        required=False,
        label="Uncertainty (km)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "any",
                "id": "range_to_sat_uncert_km",
            }
        ),
    )
    range_rate_sat_km_s = forms.FloatField(
        required=False,
        label="Range Rate of Satellite (km/s)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "any", "id": "range_rate_sat_km_s"}
        ),
    )
    range_rate_sat_uncert_km_s = forms.FloatField(
        required=False,
        label="Uncertainty (km/s)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "any",
                "id": "range_rate_sat_uncert_km_s",
            }
        ),
    )
    data_archive_link = forms.CharField(
        required=False,
        label="Data Archive Link",
        widget=forms.URLInput(
            attrs={"class": "form-control", "id": "data_archive_link"}
        ),
    )
    comments = forms.CharField(
        required=False,
        label="Comments",
        widget=forms.TextInput(
            attrs={"class": "form-control", "rows": 1, "id": "comments"}
        ),
    )
    mpc_code = forms.CharField(
        required=False,
        label="MPC Observatory Code",
        widget=forms.TextInput(attrs={"class": "form-control", "id": "mpc_code"}),
    )

    output = forms.CharField(
        required=False,
        label="Output",
        widget=forms.Textarea(
            attrs={
                "class": "form-control form-control-output",
                "rows": 10,
                "readonly": "readonly",
                "id": "output",
            }
        ),
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
