document.addEventListener('DOMContentLoaded', function() {
    // Handle server-side pagination (data_view.html)
    $('#obsTable').on('click-row.bs.table', function (e, row, $element) {
        handleObservationClick(row.observation_id, true);
    });

    // Handle client-side data (index, search, etc.)
    $(document).on('click', '[data-bs-toggle="modal"][data-bs-target="#obsModal"], #showObsModal', function(e) {
        var observationId = $(this).data('observation-id');
        handleObservationClick(observationId, false);
    });
});

function handleObservationClick(observationId, showModal) {
    fetch(`/observation/${observationId}/`)
    .then(response => response.json())
    .then(observation => {
        populateModalFields(observation);
        if (showModal) {
            var obsModal = new bootstrap.Modal(document.getElementById('obsModal'));
            obsModal.show();
        }
    })
    .catch(error => console.error('Error fetching observation data:', error));
}

function populateModalFields(observation) {
    var satelliteDataViewUrl = '/satellite/' + observation.satellite_id.sat_number + '/';
    var apparent_mag_uncert = window.NumberFormatting.roundUncertainty(observation.apparent_mag_uncert);
    var apparent_mag = window.NumberFormatting.roundMagnitude(observation.apparent_mag, apparent_mag_uncert);

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

    // Add launch link only if there's an international designator
    const launchLinkContainer = document.getElementById('launch_link_container');
    if (observation.satellite_id.intl_designator) {
        const baseDesignator = observation.satellite_id.intl_designator.slice(0, 8);
        launchLinkContainer.innerHTML = `<a href="/launch/${baseDesignator}/">View other objects from this launch</a>`;
    } else {
        launchLinkContainer.innerHTML = '';
    }
}

function populateIfExists(elementId, object) {
    if (object.hasOwnProperty(elementId) && document.getElementById(elementId)) {
        document.getElementById(elementId).textContent = object[elementId];
    }
}
