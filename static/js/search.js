$(function() {
    // Formatter functions
    window.magnitudeFormatter = function(value, row) {
        if (value === null || value === undefined) return '';
        const uncertainty = row.apparent_mag_uncert;
        return window.NumberFormatting.roundMagnitude(value, window.NumberFormatting.roundUncertainty(uncertainty));
    };

    window.numberFormatter = function(value, row) {
        if (value === null || value === undefined) return '';
        // Convert to number and round to max 4 decimal places, then convert back to string to remove trailing zeros
        return Number(Number(value).toFixed(4)).toString();
    };

    // Initialize Bootstrap Table
    var $table = $('#obsTable');

    if ($table.length) {
        $table.bootstrapTable({
            pagination: true,
            sidePagination: 'server',
            pageList: [25, 50, 100, 200],
            pageSize: 25,
            sortName: 'date_added',
            sortOrder: 'desc',
            search: true,
            searchOnEnterKey: false,
            trimOnSearch: true,
            searchable: true,
            paginationVAlign: 'bottom',
            paginationHAlign: 'right',
            paginationDetailHAlign: 'left',
            method: 'POST',
            contentType: 'application/x-www-form-urlencoded',
            onClickRow: function(row) {
                if (row.id) {
                    var obsModal = new bootstrap.Modal(document.getElementById('obsModal'));
                    handleObservationClick(row.id, true);
                }
            },
            queryParams: function(params) {
                // Get the form data
                const formData = new FormData(document.querySelector('form[action="' + window.SEARCH_URL + '"]'));
                const searchParams = Object.fromEntries(formData);

                // Show loading indicator
                document.getElementById('searchLoadingIndicator').style.display = 'block';

                // Map table field names to model field names for sorting
                const fieldMapping = {
                    'date_added': 'date_added',
                    'satellite_name': 'satellite_id__sat_name',
                    'satellite_number': 'satellite_id__sat_number',
                    'obs_time_utc': 'obs_time_utc',
                    'apparent_mag': 'apparent_mag',
                    'obs_filter': 'obs_filter',
                    'obs_lat_deg': 'location_id__obs_lat_deg',
                    'obs_long_deg': 'location_id__obs_long_deg',
                    'obs_alt_m': 'location_id__obs_alt_m',
                    'obs_mode': 'obs_mode'
                };

                return {
                    ...searchParams,
                    limit: params.limit,
                    offset: params.offset,
                    sort: fieldMapping[params.sort] || params.sort,
                    order: params.order,
                    search: params.search,
                    _csrf: document.querySelector('[name=csrfmiddlewaretoken]').value
                };
            },
            onLoadSuccess: onLoadSuccess,
            onLoadError: onLoadError
        });

        // Handle form submission
        const form = document.querySelector(`form[action="${window.SEARCH_URL}"]`);
        if (form) {
            form.addEventListener('submit', function(e) {
                // Allow the form to submit normally if no table exists
                if (!$table.length) {
                    return true;
                }

                e.preventDefault(); // Prevent default form submission

                // Show loading indicator
                document.getElementById('searchLoadingIndicator').style.display = 'block';

                // Reset table search and refresh with form data
                $table.bootstrapTable('resetSearch');
                $table.bootstrapTable('refresh', {
                    url: window.SEARCH_URL,
                    pageNumber: 1,
                    query: {}
                });
            });
        }
    }
});

function onLoadSuccess(data) {
    $('#searchLoadingIndicator').hide();

    // Update total results message
    if (data.total_results > 0) {
        $('#totalResultsMessage').html(`<p class="text-muted">Found ${data.total_results} observations</p>`);
    } else {
        $('#totalResultsMessage').empty();
    }
}

function onLoadError(status, res) {
    $('#searchLoadingIndicator').hide();
    $('#totalResultsMessage').empty();
}
