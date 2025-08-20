// Clear output text area
var clearOutputButton = document.getElementById('clear-output');
if (clearOutputButton) {
    clearOutputButton.addEventListener('click', function () {
        $('#output').val("");
        $('#output').trigger('input');
        //$('#download-csv').prop('disabled', true);
        $('#clear-output').prop('disabled', true);
    }
    )
};


// Add a new row to the output field when the addDataRow button is clicked
var addDataRowButton = document.getElementById('addDataRow');
if (addDataRowButton) {
    addDataRowButton.addEventListener('click', function () {

        // get the current contents of the form
        var formValues = {
            satellite_name: $('#sat_name').val(),
            norad_cat_id: $('#sat_number').val(),
            observing_mode: $('#obs_mode').val(),
            obs_date_year: $('#obs_date_year').val(),
            obs_date_month: $('#obs_date_month').val(),
            obs_date_day: $('#obs_date_day').val(),
            obs_date_hour: $('#obs_date_hour').val(),
            obs_date_min: $('#obs_date_min').val(),
            obs_date_sec: $('#obs_date_sec').val(),
            observation_time_uncertainty_sec: $('#obs_date_uncert').val(),
            apparent_magnitude: $('#apparent_mag').val(),
            apparent_magnitude_uncertainty: $('#apparent_mag_uncert').val(),
            not_detected: $('#not_detected').is(':checked'),
            limiting_magnitude: $('#limiting_magnitude').val(),
            instrument: $('#instrument').val(),
            observer_latitude_deg: $('#observer_latitude_deg').val(),
            observer_longitude_deg: $('#observer_longitude_deg').val(),
            observer_altitude_m: $('#observer_altitude_m').val(),
            observing_filter: $('#filter').val(),
            observer_orcid: $('#observer_orcid').val(),
            observer_email: $('#observer_email').val(),
            satellite_right_ascension_deg: $('#sat_ra_deg').val(),
            satellite_declination_deg: $('#sat_dec_deg').val(),
            sigma_2_ra: $('#sigma_2_ra').val(),
            sigma_ra_sigma_dec: $('#sigma_ra_sigma_dec').val(),
            sigma_2_dec: $('#sigma_2_dec').val(),
            range_to_satellite_km: $('#range_to_sat_km').val(),
            range_to_satellite_uncertainty_km: $('#range_to_sat_uncert_km').val(),
            range_rate_of_satellite_km_per_sec: $('#range_rate_sat_km_s').val(),
            range_rate_of_satellite_uncertainty_km_per_sec: $('#range_rate_sat_uncert_km_s').val(),
            data_archive_link: $('#data_archive_link').val(),
            comments: $('#comments').val(),
            mpc_code: $('#mpc_code').val(),
        };

        // Clear form values that change between adding observations
        $('#sat_name').val('');
        $('#sat_number').val('');
        $('#obs_date_year').val('');
        $('#obs_date_month').val('');
        $('#obs_date_day').val('');
        $('#obs_date_hour').val('');
        $('#obs_date_min').val('');
        $('#obs_date_sec').val('');
        $('#obs_date_uncert').val('');
        $('#apparent_mag').val('');
        $('#apparent_mag_uncert').val('');
        $('#not_detected').prop('checked', false);
        $('#sat_ra_deg').val('');
        $('#sat_dec_deg').val('');
        $('#sigma_2_ra').val('');
        $('#sigma_ra_sigma_dec').val('');
        $('#sigma_2_dec').val('');
        $('#range_to_sat_km').val('');
        $('#range_to_sat_uncert_km').val('');
        $('#range_rate_sat_km_s').val('');
        $('#range_rate_sat_uncert_km_s').val('');
        $('#comments').val('');

        //create a csv row from that data
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
        ];

        var csvString = '';
        header.forEach(function (item, index) {
            if (item === 'observation_time_utc') {
                // Combine the date and time values into a single string
                var date = new Date(Date.UTC(formValues['obs_date_year'], formValues['obs_date_month'] - 1, formValues['obs_date_day'], formValues['obs_date_hour'], formValues['obs_date_min'], formValues['obs_date_sec']));
                csvString += date.toISOString();
            } else {
                // Append the form value to the string
                var value = formValues[item];
                if (item === 'comments' || item === 'observer_orcid') {
                    // if item is not empty
                    if (value && value.includes(',')) {
                        // Enclose the value in quotes if the item is 'comments', 'data_archive_link', or 'observer_orcid'
                        value = '"' + value + '"';
                    }
                }
                csvString += value;
            }

            // Add a comma after each value except the last one
            if (index < header.length - 1) {
                csvString += ',';
            }
        });

        //append that row to the output field
        var outputField = document.getElementById('output');
        outputField.value += csvString + '\n';
        $(outputField).trigger('input');
        $('#clear-output').prop('disabled', false);
    }
    )
};

$('#observer_orcid').blur(function () {
    var observer_orcid = $(this).val();
    $.post('/last_observer_location/', { 'observer_orcid': observer_orcid }, function (data) {
        if (!data.error) {
            $('#observer_altitude_m').val(data.observer_altitude_m);
            $('#observer_latitude_deg').val(data.observer_latitude_deg);
            $('#observer_longitude_deg').val(data.observer_longitude_deg);
        }
    });
});

$(document).ready(function () {
$('[data-toggle="tooltip"]').tooltip();
    // Function to validate a single field
    function validateField(field) {
        var isValid = true;
        var value = $(field).val();
        var id = $(field).attr('id');
        var errorMessage = '';

        // Custom validation logic based on field ID
        switch (id) {
            case 'observer_email':
                if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                    isValid = false;
                    errorMessage = 'Invalid email address.';
                }
                break;
            case 'observer_orcid':
                if (value && !/^\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]$/.test(value)) {
                    isValid = false;
                    errorMessage = 'Invalid ORCID format.';
                } else if (value) {
                    // Normalize ORCID by converting to uppercase
                    var normalizedValue = value.toUpperCase();
                    if (normalizedValue !== value) {
                        $(field).val(normalizedValue);
                    }
                }
                break;
            case 'sat_number':
                if (value && (value < 0 || value > 999999)) {
                    isValid = false;
                    errorMessage = 'NORAD ID must be between 0 and 999999.';
                }
                break;
            case 'obs_date_year':
                if (value && (value < 1957 || value > 99999)) {
                    isValid = false;
                    errorMessage = 'Value must be between 1957 and 99999.';
                }
                break;
            case 'obs_date_month':
                if (value && (value < 1 || value > 12)) {
                    isValid = false;
                    errorMessage = 'Value must be between 1 and 12.';
                }
                break;
            case 'obs_date_day':
                if (value && (value < 1 || value > 31)) {
                    isValid = false;
                    errorMessage = 'Value must be between 1 and 31.';
                }
                break;
            case 'obs_date_hour':
                if (value && (value < 0 || value > 24)) {
                    isValid = false;
                    errorMessage = 'Value must be between 0 and 24.';
                }
                break;
            case 'obs_date_min':
            case 'obs_date_sec':
                if (value && (value < 0 || value > 60)) {
                    isValid = false;
                    errorMessage = 'Value must be between 0 and 60.';
                }
                break;
            case 'observer_latitude_deg':
                if (value && (value < -90 || value > 90)) {
                    isValid = false;
                    errorMessage = 'Value must be between -90 and 90.';
                }
                break;
            case 'observer_longitude_deg':
                if (value && (value < -180 || value > 180)) {
                    isValid = false;
                    errorMessage = 'Value must be between -180 and 180.';
                }
                break;
            case 'observer_altitude_m':
                if (value && value < -420) {
                    isValid = false;
                    errorMessage = 'Value must be greater than or equal to -420.';
                }
                break;
            case 'sat_ra_deg':
                if (value && (value < 0 || value > 360)) {
                    isValid = false;
                    errorMessage = 'Value must be between 0 and 360.';
                }
                break;
            case 'sat_dec_deg':
                if (value && (value < -90 || value > 90)) {
                    isValid = false;
                    errorMessage = 'Value must be between -90 and 90.';
                }
                break;
        }

        // Display or hide error message using Bootstrap validation classes
        if (!isValid) {
            $(field).addClass('is-invalid');
            if (!$(field).next('.invalid-feedback').length) {
                $(field).after('<div class="invalid-feedback">' + errorMessage + '</div>');
            }
        } else {
            $(field).removeClass('is-invalid');
            $(field).next('.invalid-feedback').remove();
        }

        return isValid;
    }
     // Attach blur event listeners to the form fields
     $('#observer_email, #observer_orcid, #sat_number, #obs_date_year, #obs_date_month, #obs_date_day, #obs_date_hour, #obs_date_min, #obs_date_sec, #observer_latitude_deg, #observer_longitude_deg, #observer_altitude_m, #sat_ra_deg, #sat_dec_deg').on('blur', function () {
        validateField(this);
    });


function validateForm() {
    var isFormValid = true;

    // Check if all required inputs have a value
    $('form :input[required]').each(function () {
        if (!$(this).val()) {
            isFormValid = false;
        }
    });

    // Validate each field individually
    $('#observer_email, #observer_orcid, #sat_number, #obs_date_year, #obs_date_month, #obs_date_day, #obs_date_hour, #obs_date_min, #obs_date_sec, #observer_latitude_deg, #observer_longitude_deg, #observer_altitude_m').each(function () {
        if (!validateField(this)) {
            isFormValid = false;
        }
    });

    // Custom validation for apparent magnitude and not detected
    var apparentMag = $('#apparent_mag').val();
    var apparentMagUncert = $('#apparent_mag_uncert').val();
    var notDetected = $('#not_detected').is(':checked');
    if (!(apparentMag && apparentMagUncert) && !notDetected) {
        isFormValid = false;
    }

    if (isFormValid) {
        $('#addDataRow').prop('disabled', false);
    } else {
        $('#addDataRow').prop('disabled', true);
    }
}

$('form :input').on('input', validateForm);
$('#not_detected').on('change', validateForm);


$('#output').on('input', function () {
    if ($(this).val()) {
        $('#download-csv').prop('disabled', false);
    } else {
        $('#download-csv').prop('disabled', true);
    }
});
});

$('#not_detected').change(function () {
    if (this.checked) {
        $('#apparent_mag').prop('disabled', true);
        $('#apparent_mag').prop('required', false);
        $('#apparent_mag').val(''); // Clear the input
        $('#apparent_mag_uncert').prop('disabled', true);
        $('#apparent_mag_uncert').prop('required', false);
        $('#apparent_mag_uncert').val(''); // Clear the input
    } else {
        $('#apparent_mag').prop('disabled', false);
        $('#apparent_mag').prop('required', true);
        $('#apparent_mag_uncert').prop('disabled', false);
        $('#apparent_mag_uncert').prop('required', true);
    }
});
