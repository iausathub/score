$(document).on('click', '#obsTable tr, #showObsModal', function () {
    var rowData = $(this).data('content');
    var escapedJSON = rowData.replace(/\\u0022/g, '\"').replace(/\\u002D/g, '-').replace(/b\\u0027/g, '').replace(/\\u0027/g, '');

    var observation = JSON.parse(escapedJSON);
    $('#observation_id_label').text(observation.id);
    $('#satellite_name').text(observation.satellite_id.sat_name);
    $('#satellite_number').text(observation.satellite_id.sat_number);
    $('#obs_time_utc').text(observation.obs_time_utc);
    $('#obs_time_uncert').text(observation.obs_time_uncert_sec);
    $('#date_added_label').text(observation.date_added);
    $('#apparent_mag').text(observation.apparent_mag);
    $('#apparent_mag_uncert').text(observation.apparent_mag_uncert);
    $('#obs_lat_deg').text(observation.location_id.obs_lat_deg);
    $('#obs_long_deg').text(observation.location_id.obs_long_deg);
    $('#obs_alt_m').text(observation.location_id.obs_alt_m);
    $('#obs_mode').text(observation.obs_mode);
    $('#obs_filter').text(observation.obs_filter);
    $('#obs_instrument').text(observation.instrument);
    $('#obs_orc_id').html(observation.obs_orc_id.toString().replace(/,/g, ',<br/>'));
    $('#obs_comments').text(observation.obs_comments);
    $('#mpc_code').text(observation.mpc_code);
    $('#sat_ra_deg').text(observation.sat_ra_deg);
    $('#sat_dec_deg').text(observation.sat_dec_deg);
    $('#sigma_2_ra').text(observation.sigma_2_ra);
    $('#sigma_ra_sigma_dec').text(observation.sigma_ra_sigma_dec);
    $('#sigma_2_dec').text(observation.sigma_2_dec);
    $('#range_to_sat_km').text(observation.range_to_sat_km);
    $('#range_to_sat_uncert_km').text(observation.range_to_sat_uncert_km);
    $('#range_rate_km_s').text(observation.range_rate_sat_km_s);
    $('#range_rate_uncert_km_s').text(observation.range_rate_sat_uncert_km_s);
    if (observation.data_archive_link != "") {
        $('#data_archive_link').html('<a href="' + observation.data_archive_link + '">Data link</a>');
    }
    $('#limiting_magnitude').text(observation.limiting_magnitude);
    $('#phase_angle').text(observation.phase_angle);
    $('#range_to_sat_km_satchecker').text(observation.range_to_sat_km_satchecker);
    $('#range_rate_sat_km_s_satchecker').text(observation.range_rate_sat_km_s_satchecker);
    $('#sat_ra_deg_satchecker').text(observation.sat_ra_deg_satchecker);
    $('#sat_dec_deg_satchecker').text(observation.sat_dec_deg_satchecker);
    $('#ddec_deg_s_satchecker').text(observation.ddec_deg_s_satchecker);
    $('#dra_cosdec_deg_s_satchecker').text(observation.dra_cosdec_deg_s_satchecker);
    $('#alt_deg_satchecker').text(observation.alt_deg_satchecker);
    $('#az_deg_satchecker').text(observation.az_deg_satchecker);
    $('#illuminated').text(observation.illuminated);
});
