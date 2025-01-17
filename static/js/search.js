document.addEventListener('DOMContentLoaded', function() {
    // listen for form submit
    const form = document.querySelector(`form[action="${window.SEARCH_URL}"]`);

    if (form) {
        form.addEventListener('submit', function() {
            document.getElementById('searchLoadingIndicator').style.display = 'block';

            // hide existing results
            const tableContainer = document.querySelector('.table-container');
            if (tableContainer) {
                tableContainer.style.display = 'none';
            }
        });
    }
});
