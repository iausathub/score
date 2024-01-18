from django import forms
from django.forms import Form


class UploadObservationFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class SearchForm(Form):
    sat_name = forms.CharField(
        max_length=200,
        required=False,
        label="Satellite Name",
        widget=forms.TextInput(
            attrs={"placeholder": "Enter Satellite Name", "class": "form-control"}
        ),
    )
    sat_number = forms.IntegerField(
        required=False,
        label="Satellite Number",
        widget=forms.NumberInput(
            attrs={"min": 0, "max": 99999, "class": "form-control"}
        ),
    )
    obs_mode = forms.CharField(
        max_length=200,
        required=False,
        label="Observation Mode",
        widget=forms.TextInput(
            attrs={"placeholder": "Enter Observation Mode", "class": "form-control"}
        ),
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
        widget=forms.TextInput(
            attrs={"placeholder": "Constellation Name", "class": "form-control"}
        ),
    )
    observation_id = forms.IntegerField(
        required=False,
        label="Observation ID",
        widget=forms.TextInput(attrs={"type": "number", "class": "form-control"}),
    )
