// Lookup the NORAD ID based on the satellite name (and vice versa)
$('#name-id-lookup').on('submit', function (event) {
	event.preventDefault(); // Prevent the form from being submitted normally

	var satellite_name = $('#satellite_name').val();
	var satellite_id = $('#satellite_id').val();

	$.post('/name-id-lookup', { 'satellite_name': satellite_name, 'satellite_id': satellite_id }, function (data) {
		if (!data.error) {
			$('#satellite_id').val(data.norad_id);
			$('#satellite_name').val(data.satellite_name);
			$('#lookup_error').text('');
		} else {
			$('#lookup_error').text(data.error);
		}
	});
});


// Lookup the satellite position based on the observer location, date/time, and satellite identifier
$('#satellite_pos_lookup').on('submit', function (event) {
	event.preventDefault(); // Prevent the form from being submitted normally

	// make sure the results and error messages are hidden if they were visible
	document.getElementById('results').hidden = true;
	$('#sat_pos_lookup_error').text("");

	// reset the results just in case
	$('#pos_check_ra').text("");
	$('#pos_check_dec').text("");
	$('#pos_check_altitude').text("");
	$('#pos_check_azimuth').text("");
	$('#pos_check_date').text("");
	$('#pos_check_name').text("");
	$('#pos_check_id').text("");

	var obs_lat = $('#obs_lat').val();
	var obs_long = $('#obs_long').val();
	var obs_alt = $('#obs_alt').val();
	var day = $('#day').val();
	var month = $('#month').val();
	var year = $('#year').val();
	var hour = $('#hour').val();
	var minutes = $('#minutes').val();
	var seconds = $('#seconds').val();
	var satellite_id = $('#norad_id').val();
	var satellite_name = $('#sat_name').val()
	$.post('/satellite-pos-lookup', {
		'obs_lat': obs_lat,
		'obs_long': obs_long,
		'obs_alt': obs_alt,
		'day': day,
		'month': month,
		'year': year,
		'hour': hour,
		'minutes': minutes,
		'seconds': seconds,
		'satellite_id': satellite_id,
		'satellite_name': satellite_name
	}, function (data) {
		if (!data.error) {
			$('#pos_check_ra').text(data.ra);
			$('#pos_check_dec').text(data.dec);
			$('#pos_check_altitude').text(data.altitude);
			$('#pos_check_azimuth').text(data.azimuth);
			$('#pos_check_date').text(data.tle_date);
			$('#pos_check_name').text(data.satellite_name);
			$('#pos_check_id').text(data.norad_id);
			$('#sat_pos_lookup_error').text("");
			document.getElementById('results').hidden = false;
		} else {
			document.getElementById('results').hidden = true;
			$('#sat_pos_lookup_error').text(data.error);
		}
	});
});

$('#satellite_pos_lookup').on('reset', function (event) {
	$('#results').prop('hidden', true);
	$('#pos_check_ra').text("");
	$('#pos_check_dec').text("");
	$('#pos_check_altitude').text("");
	$('#pos_check_azimuth').text("");
	$('#pos_check_date').text("");
	$('#pos_check_name').text("");
	$('#pos_check_id').text("");
	$('#sat_pos_lookup_error').text("");
});
