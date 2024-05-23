import pytest

from repository.tasks import UploadError, process_upload


@pytest.mark.django_db
def test_process_upload_valid_data(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    data = [
        [
            "PELICAN 3001",
            "58296",
            "2020-05-08T21:42:54.572Z",
            0.001,
            6.0418,
            0.0952,
            52.01,
            4.49085,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "michelle.dadighat@noirlab.edu",
            "0000-0001-6659-9253",
            185.4465171,
            25.69768917,
            0,
            0,
            0,
            571.894,
            0,
            0,
            0,
            "5-frame average; lim mag of instrument",
            "",
            "",
        ]
    ]
    result = process_upload(data)
    assert result["status"] == "success"
    assert isinstance(result["obs_ids"], list)
    assert isinstance(result["date_added"], str)
    assert isinstance(result["email"], str)


@pytest.mark.django_db
def test_process_upload_sample_data(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    data = [
        [
            "SATHUB-SATELLITE",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
    ]
    with pytest.raises(
        UploadError, match="File contains sample data. Please upload a valid file."
    ):
        process_upload(data)


@pytest.mark.django_db
def test_process_upload_incorrect_number_of_fields(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    # 26 fields instead of 27
    data = [
        [
            "SAT-123",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
    ]
    with pytest.raises(UploadError, match="Incorrect number of fields in csv file."):
        process_upload(data)


@pytest.mark.django_db
def test_process_upload_value_error(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    # Satellite number is "test" instead of an integer
    data = [
        [
            "PELICAN 3001",
            "test",
            "2020-05-08T21:42:54.572Z",
            0.001,
            6.0418,
            0.0952,
            52.01,
            4.49085,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "michelle.dadighat@noirlab.edu",
            "0000-0001-6659-9253",
            185.4465171,
            25.69768917,
            0,
            0,
            0,
            571.894,
            0,
            0,
            0,
            "5-frame average; lim mag of instrument",
            "",
            "",
        ]
    ]
    with pytest.raises(UploadError):
        process_upload(data)


@pytest.mark.django_db
def test_process_upload_validation_error(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    # ORCID is 0 instead of in the format 0000-0000-0000-0000
    data = [
        [
            "PELICAN 3001",
            58296,
            "2020-05-08T21:42:54.572Z",
            0.001,
            6.0418,
            0.0952,
            52.01,
            4.49085,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "michelle.dadighat@noirlab.edu",
            "0",
            185.4465171,
            25.69768917,
            0,
            0,
            0,
            571.894,
            0,
            0,
            0,
            "5-frame average; lim mag of instrument",
            "",
            "",
        ]
    ]
    with pytest.raises(UploadError):
        process_upload(data)


@pytest.mark.django_db
def test_process_upload_general_exception(mocker):
    # Satellite not visible - date changed from May 8 to May 9
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    data = [
        [
            "PELICAN 3001",
            "58296",
            "2024-05-09T21:42:54.572Z",
            0.001,
            6.0418,
            0.0952,
            52.01,
            4.49085,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "michelle.dadighat@noirlab.edu",
            "0000-0001-6659-9253",
            185.4465171,
            25.69768917,
            0,
            0,
            0,
            571.894,
            0,
            0,
            0,
            "5-frame average; lim mag of instrument",
            "",
            "",
        ]
    ]
    with pytest.raises(UploadError):
        process_upload(data)


@pytest.mark.django_db
def test_process_upload_name_id_mismatch(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    data = [
        [
            "PELICAN 3001",
            "58295",
            "2024-05-08T21:42:54.572Z",
            0.001,
            6.0418,
            0.0952,
            52.01,
            4.49085,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "michelle.dadighat@noirlab.edu",
            "0000-0001-6659-9253",
            185.4465171,
            25.69768917,
            0,
            0,
            0,
            571.894,
            0,
            0,
            0,
            "5-frame average; lim mag of instrument",
            "",
            "",
        ]
    ]

    with pytest.raises(UploadError):
        process_upload(data)
