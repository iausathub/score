import pytest
from django.utils import timezone

from repository.models import Satellite
from repository.tasks import UploadError, process_upload


@pytest.mark.django_db
def test_process_upload_valid_data(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    data = [
        [
            "ACS 3",
            "59588",
            "2024-10-03T19:00:27.319Z",
            0.001,
            6.6830102,
            0.096618345,
            52.15,
            4.49,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "test@example.com",
            "0000-0001-6659-9253",
            342.9184541,
            16.81681335,
            0,
            0,
            0,
            1421.885,
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
            "test@example.com",
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
            "test@example.com",
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
            "test@example.com",
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
            "test@example.com",
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
def test_process_upload_existing_satellite(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")

    # Create existing satellite with name
    Satellite.objects.create(
        sat_name="STARLINK-1234",
        sat_number="59588",
        date_added=timezone.now(),
        intl_designator="2024-001A",
    )

    # Test data with same number but no name (archival case)
    data = [
        [
            "",
            "59588",
            "2024-10-03T19:00:27.319Z",
            0.001,
            6.6830102,
            0.096618345,
            52.15,
            4.49,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "test@example.com",
            "0000-0001-6659-9253",
            342.9184541,
            16.81681335,
            0,
            0,
            0,
            1421.885,
            0,
            0,
            0,
            "5-frame average",
            "",
            "",
        ]
    ]

    result = process_upload(data)

    # Verify satellite wasn't duplicated
    assert Satellite.objects.count() == 1

    # Verify existing satellite was used and maintained its data
    satellite = Satellite.objects.get(sat_number="59588")
    assert satellite.sat_name == "STARLINK-1234"
    assert satellite.intl_designator == "2024-001A"
    assert result["status"] == "success"


@pytest.mark.django_db
def test_process_upload_update_empty_name(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")

    # Create satellite with empty name
    Satellite.objects.create(sat_name="", sat_number="59588", date_added=timezone.now())

    # Test data with name for existing number
    data = [
        [
            "ACS 3",
            "59588",
            "2024-10-03T19:00:27.319Z",
            0.001,
            6.6830102,
            0.096618345,
            52.15,
            4.49,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "test@example.com",
            "0000-0001-6659-9253",
            342.9184541,
            16.81681335,
            0,
            0,
            0,
            1421.885,
            0,
            0,
            0,
            "5-frame average",
            "",
            "",
        ]
    ]

    result = process_upload(data)

    # Verify satellite name was updated
    satellite = Satellite.objects.get(sat_number="59588")
    assert satellite.sat_name == "ACS 3"
    assert result["status"] == "success"


@pytest.mark.django_db
def test_process_upload_new_satellites(mocker):
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")

    data = [
        [
            "ACS 3",
            "59588",
            "2024-10-03T19:00:27.319Z",
            0.001,
            6.6830102,
            0.096618345,
            52.15,
            4.49,
            8,
            10,
            "WATEC 902H2 Supreme + 1.2/85 mm",
            "CCD",
            "CLEAR",
            "test@example.com",
            "0000-0001-6659-9253",
            185.4465171,
            16.81681335,
            0,
            0,
            0,
            1421.885,
            0,
            0,
            0,
            "5-frame average",
            "",
            "",
        ]
    ]

    result = process_upload(data)

    # Verify satellite name was updated
    satellite = Satellite.objects.get(sat_number="59588")
    assert satellite.sat_name == "ACS 3"
    assert result["status"] == "success"

    # No name
    data = [
        [
            "",
            "58296",
            "2015-05-08T21:42:54.572Z",
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
            "test@example.com",
            "0000-0001-6659-9253",
            185.2311116,
            26.15498563,
            0,
            0,
            0,
            571.894,
            0,
            0,
            0,
            "5-frame average",
            "",
            "",
        ]
    ]
    result = process_upload(data)
    assert result["status"] == "success"
    assert Satellite.objects.count() == 2
    assert Satellite.objects.get(sat_number="58296").sat_name == ""

    data = [
        [
            "",
            "58013",
            "2024-05-08T02:22:45.000Z",
            1,
            4,
            0.2,
            36.062,
            -91.688,
            185,
            0,
            "none",
            "VISUAL",
            "CLEAR",
            "test@example.com",
            "0009-0001-8403-8334",
            185.2311116,
            26.15498563,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            "test obs",
            "",
            "",
        ]
    ]
    result = process_upload(data)
    assert result["status"] == "success"
    assert Satellite.objects.count() == 3
    assert Satellite.objects.get(sat_number="58013").sat_name == "KUIPER-P2"
