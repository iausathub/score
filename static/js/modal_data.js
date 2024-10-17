document.addEventListener('DOMContentLoaded', function() {
    // Handle server-side pagination (data_view.html)
    $('#obsTable').on('click-row.bs.table', function (e, row, $element) {
        handleObservationClick(row, true);
    });

    // Handle client-side data (index, search, etc.)
    $(document).on('click', '[data-bs-toggle="modal"][data-bs-target="#obsModal"], #showObsModal', function(e) {
        var observationJson = $(this).data('content');
        handleObservationClick(observationJson, false);
    });
});

function handleObservationClick(data, showModal) {
    var observation = parseObservationData(data);
    if (!observation) return;

    populateModalFields(observation);

    if (showModal) {
        var obsModal = new bootstrap.Modal(document.getElementById('obsModal'));
        obsModal.show();
    }
}

function parseObservationData(data) {
    if (typeof data === 'string') {
        // For client-side data (index, search, etc.)
        var escapedJSON = data.replace(/\\u0022/g, '\"').replace(/\\u002D/g, '-').replace(/b\\u0027/g, '').replace(/\\u0027/g, '');
        return JSON.parse(escapedJSON);
    } else if (data && data.observation_json) {
        // For server-side pagination (currently only data_view.html)
        return JSON.parse(data.observation_json);
    }
}

function populateModalFields(observation) {
    var satelliteDataViewUrl = '/satellite/' + observation.satellite_id.sat_number + '/';
    var apparent_mag_uncert = roundUncertainty(observation.apparent_mag_uncert);
    var apparent_mag = roundMagnitude(observation.apparent_mag, apparent_mag_uncert);

    document.getElementById('observation_id_label').textContent = observation.id;
    document.getElementById('satellite_name').innerHTML = '<a href="' + satelliteDataViewUrl + '">'+ observation.satellite_id.sat_name +'</a>';
    document.getElementById('satellite_number').textContent = observation.satellite_id.sat_number;
    document.getElementById('intl_designator').textContent = observation.satellite_id.intl_designator;
    document.getElementById('obs_time_utc').textContent = observation.obs_time_utc;
    document.getElementById('obs_time_uncert').textContent = observation.obs_time_uncert_sec;
    document.getElementById('date_added_label').textContent = observation.date_added;
    document.getElementById('apparent_mag').textContent = apparent_mag;
    document.getElementById('apparent_mag_uncert').textContent = apparent_mag_uncert;
    document.getElementById('obs_lat_deg').textContent = observation.location_id.obs_lat_deg;
    document.getElementById('obs_long_deg').textContent = observation.location_id.obs_long_deg;
    document.getElementById('obs_alt_m').textContent = observation.location_id.obs_alt_m;
    document.getElementById('obs_mode').textContent = observation.obs_mode;
    document.getElementById('obs_filter').textContent = observation.obs_filter;
    document.getElementById('obs_instrument').textContent = observation.instrument;
    document.getElementById('obs_orc_id').innerHTML = observation.obs_orc_id.toString().replace(/,/g, ',<br/>');

    // Populate additional fields
    populateIfExists('obs_comments', observation);
    populateIfExists('mpc_code', observation);
    populateIfExists('sat_ra_deg', observation);
    populateIfExists('sat_dec_deg', observation);
    populateIfExists('sigma_2_ra', observation);
    populateIfExists('sigma_ra_sigma_dec', observation);
    populateIfExists('sigma_2_dec', observation);
    populateIfExists('range_to_sat_km', observation);
    populateIfExists('range_to_sat_uncert_km', observation);
    populateIfExists('range_rate_km_s', observation);
    populateIfExists('range_rate_uncert_km_s', observation);
    populateIfExists('limiting_magnitude', observation);
    populateIfExists('phase_angle', observation);
    populateIfExists('range_to_sat_km_satchecker', observation);
    populateIfExists('range_rate_sat_km_s_satchecker', observation);
    populateIfExists('sat_ra_deg_satchecker', observation);
    populateIfExists('sat_dec_deg_satchecker', observation);
    populateIfExists('ddec_deg_s_satchecker', observation);
    populateIfExists('dra_cosdec_deg_s_satchecker', observation);
    populateIfExists('alt_deg_satchecker', observation);
    populateIfExists('az_deg_satchecker', observation);
    populateIfExists('illuminated', observation);

    if (observation.data_archive_link && observation.data_archive_link !== "") {
        document.getElementById('data_archive_link').innerHTML = '<a href="' + observation.data_archive_link + '">Data link</a>';
    } else {
        document.getElementById('data_archive_link').textContent = "";
    }
}

function populateIfExists(elementId, object) {
    if (object.hasOwnProperty(elementId) && document.getElementById(elementId)) {
        document.getElementById(elementId).textContent = object[elementId];
    }
}

function roundUncertainty(uncertainty) {
    if (uncertainty === 0) return "0";

    // order of magnitude of the uncertainty
    const magnitude = Math.floor(Math.log10(uncertainty));
    const firstDigit = uncertainty / Math.pow(10, magnitude);

    // Use 2 significant figures for values starting with 1 or 2, otherwise use 1
    const sigFigs = firstDigit < 3 ? 2 : 1;

    const uncertaintyStr = uncertainty.toString();
    if (uncertaintyStr.replace(/^0\./, '').length <= sigFigs) {
        return uncertaintyStr;
    }

    // scale for rounding to desired significant figures
    const scale = Math.pow(10, sigFigs - magnitude - 1);

    // round and convert back to a string to remove unneeded zeros
    return (Math.round(uncertainty * scale) / scale).toString();
}

function roundMagnitude(value, uncertainty) {
    if (uncertainty === 0) return value.toString();

    // get number of decimal places in uncertainty
    const uncertaintyStr = uncertainty.toString();
    const uncertaintyDecimalPlaces = (uncertaintyStr.split('.')[1] || '').length;

    // get the decimal places in the original value
    const valueDecimalPlaces = (value.toString().split('.')[1] || '').length;

    // use at least one decimal place for uncertainties between 0.1 and 1
    const minDecimalPlaces = (uncertainty >= 0.1 && uncertainty < 1) ? 1 : 0;

    // confirm correct precision
    const finalDecimalPlaces = Math.max(
        minDecimalPlaces,
        Math.min(uncertaintyDecimalPlaces, valueDecimalPlaces)
    );
    return value.toFixed(finalDecimalPlaces);
}
