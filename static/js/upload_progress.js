// Progress Bar (JQuery)
$(document).ready(function() {
document.getElementById('progress-bar').hidden = false;
function customResult(resultElement, result) {
    document.getElementById('upload_btn').disabled = false;
    document.getElementById('upload_ctrl').disabled = false;

    $('#upload_ctrl').val('');
    if (result.status == "success") {
        var date = new Date(result.date_added);
        var formattedDate = date.toUTCString().replace('GMT', 'UTC');

        document.getElementById('obs_added_text').innerText =
            result.obs_ids.length + " observation(s) added to the database at " + formattedDate + ".";
        document.getElementById('success_message').hidden = false;
        //remove progress bar
        document.getElementById('progress-bar').hidden = true;
        document.getElementById('progress-bar-message').hidden = true;
        document.getElementById('download_obs_ids').value = result.obs_ids;
        document.getElementById('email').innerText = result.email;
    }
    else {
        $(resultElement).append(
            $('<br>')
        );
        var formattedResult = result.replace(/\n/g, '<br>');
        $(resultElement).append(
            $('<p>').html(formattedResult)
        );
    }
}

function customError(progressBarElement, progressBarMessageElement) {
    progressBarElement.style.backgroundColor = '#c21e1b';
    progressBarMessageElement.innerHTML = 'Upload failed - check the error and try again.';
}

$(function () {
    // Initialize the progress bar
    CeleryProgressBar.initProgressBar(progressUrl, {
        onResult: customResult,
        defaultMessages: {
            waiting: "Waiting for upload to start...",
            started: "Upload started...",
        },
        onError: customError,
    })
});
});
