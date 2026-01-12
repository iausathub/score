import os
import uuid

import pytest
from django.utils import timezone
from ninja.testing import TestClient

from repository.api import api
from repository.models import APIKey
from repository.tasks import process_upload_api


@pytest.fixture
def api_key():
    """Create a test API key"""
    api_key_obj, plaintext_key = APIKey.create_key(
        name="Test User",
        email="test@example.com",
        orcid_id="0000-0000-0000-0000",
        notes="Test API key",
    )
    # Return both the object and the plaintext key for testing
    return api_key_obj, plaintext_key


@pytest.mark.django_db
def test_upload_observation(mocker, api_key):
    """Test uploading one observation with authentication"""
    os.environ["NINJA_SKIP_REGISTRY"] = "1"
    client = TestClient(api)
    api_key_obj, plaintext_key = api_key

    # Mock the Celery task response
    mock_task = mocker.Mock()
    test_task_id = str(uuid.uuid4())
    mock_task.task_id = test_task_id
    mocker.patch(
        "repository.api.upload.process_upload_api.apply_async",
        return_value=mock_task,
    )

    batch_id = str(uuid.uuid4())
    observation_data = {
        "observations": [
            {
                "obs_time_utc": "2024-01-01T00:00:00Z",
                "obs_time_uncert_sec": 0.1,
                "instrument": "TEST-SCOPE",
                "obs_mode": "CCD",
                "obs_filter": "Clear",
                "obs_email": "test@example.com",
                "obs_orc_id": ["0000-0000-0000-0000"],
                "satellite_number": 12345,
                "obs_lat_deg": 20.0,
                "obs_long_deg": -155.0,
                "obs_alt_m": 3000.0,
                "limiting_magnitude": 18.0,
            }
        ],
        "notification_email": "test@example.com",
        "batch_id": batch_id,
    }
    response = client.post(
        "/upload",
        json=observation_data,
        headers={"Authorization": f"Bearer {plaintext_key}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["batch_id"] == test_task_id
    assert "created_at" in data


@pytest.mark.django_db
def test_upload_observation_no_auth(mocker):
    """Test uploading without authentication returns 401"""
    os.environ["NINJA_SKIP_REGISTRY"] = "1"
    client = TestClient(api)

    observation_data = {
        "observations": [
            {
                "obs_time_utc": "2024-01-01T00:00:00Z",
                "obs_time_uncert_sec": 0.1,
                "instrument": "TEST-SCOPE",
                "obs_mode": "CCD",
                "obs_filter": "Clear",
                "obs_email": "test@example.com",
                "obs_orc_id": ["0000-0000-0000-0000"],
                "satellite_number": 12345,
                "obs_lat_deg": 20.0,
                "obs_long_deg": -155.0,
                "obs_alt_m": 3000.0,
                "limiting_magnitude": 18.0,
            }
        ],
        "notification_email": "test@example.com",
    }
    response = client.post("/upload", json=observation_data)
    assert response.status_code == 401


@pytest.mark.django_db
def test_upload_observation_invalid_auth(mocker):
    """Test uploading with invalid API key returns 401"""
    os.environ["NINJA_SKIP_REGISTRY"] = "1"
    client = TestClient(api)

    observation_data = {
        "observations": [
            {
                "obs_time_utc": "2024-01-01T00:00:00Z",
                "obs_time_uncert_sec": 0.1,
                "instrument": "TEST-SCOPE",
                "obs_mode": "CCD",
                "obs_filter": "Clear",
                "obs_email": "test@example.com",
                "obs_orc_id": ["0000-0000-0000-0000"],
                "satellite_number": 12345,
                "obs_lat_deg": 20.0,
                "obs_long_deg": -155.0,
                "obs_alt_m": 3000.0,
                "limiting_magnitude": 18.0,
            }
        ],
        "notification_email": "test@example.com",
    }
    response = client.post(
        "/upload",
        json=observation_data,
        headers={"Authorization": "Bearer invalid_key_12345"},
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_upload_status(mocker, api_key):
    """Test getting the status endpoint returns valid response with authentication"""
    os.environ["NINJA_SKIP_REGISTRY"] = "1"
    client = TestClient(api)
    api_key_obj, plaintext_key = api_key

    # Mock AsyncResult and Progress to avoid Redis connection
    mock_task = mocker.Mock()
    mock_task.info = None
    mocker.patch("repository.api.upload.AsyncResult", return_value=mock_task)

    mock_progress_instance = mocker.Mock()
    mock_progress_instance.get_info.return_value = {"state": "PENDING"}
    mocker.patch("repository.api.upload.Progress", return_value=mock_progress_instance)

    batch_id = uuid.uuid4()
    response = client.get(
        f"/upload/{batch_id}/status",
        headers={"Authorization": f"Bearer {plaintext_key}"},
    )
    assert response.status_code == 200
    data = response.json()
    # Should get a status for non-existent task (PENDING)
    assert "status" in data
    assert data["status"] == "PENDING"
    assert "batch_id" in data


@pytest.mark.django_db
def test_get_upload_status_no_auth(mocker):
    """Test getting the status without authentication returns 401"""
    os.environ["NINJA_SKIP_REGISTRY"] = "1"
    client = TestClient(api)

    batch_id = uuid.uuid4()
    response = client.get(f"/upload/{batch_id}/status")
    assert response.status_code == 401


@pytest.mark.django_db
def test_process_upload_api_success_task(mocker):
    """Test that the task completes with a successfully created observation"""
    # Mock all the things
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    mocker.patch("repository.tasks.send_confirmation_email")
    mocker.patch.object(process_upload_api, "update_state")

    # Mock the SatChecker response
    mock_satchecker = mocker.Mock()
    mock_satchecker.alt_deg = 15.0
    mock_satchecker.illuminated = True
    mock_satchecker.phase_angle = 15.0
    mock_satchecker.range_to_sat = 500.0
    mock_satchecker.range_rate = 0.1
    mock_satchecker.sat_ra_deg = 180.0
    mock_satchecker.sat_dec_deg = 45.0
    mock_satchecker.ddec_deg_s = 0.01
    mock_satchecker.dra_cosdec_deg_s = 0.02
    mock_satchecker.az_deg = 270.0
    mock_satchecker.satellite_name = "TEST SAT"
    mock_satchecker.intl_designator = "2024-001A"
    mock_satchecker.sat_altitude_km = 400.0
    mock_satchecker.solar_elevation_deg = -10.0
    mock_satchecker.solar_azimuth_deg = 180.0
    mocker.patch("repository.tasks.add_additional_data", return_value=mock_satchecker)

    obs_time = timezone.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Completed, with accepted observation
    observations_data = [
        {
            "satellite_name": "TEST SAT",
            "satellite_number": 12345,
            "obs_time_utc": obs_time,
            "obs_time_uncert_sec": 0.1,
            "instrument": "TEST-SCOPE",
            "obs_mode": "CCD",
            "obs_filter": "Clear",
            "obs_email": "test@example.com",
            "obs_orc_id": ["0000-0000-0000-0000"],
            "obs_lat_deg": 20.0,
            "obs_long_deg": -155.0,
            "obs_alt_m": 3000.0,
            "limiting_magnitude": 18.0,
            "apparent_mag": 6,
            "apparent_mag_uncert": 1,
            "sat_ra_deg": None,
            "sat_dec_deg": None,
            "sigma_2_ra": None,
            "sigma_2_dec": None,
            "sigma_ra_sigma_dec": None,
            "range_to_sat_km": None,
            "range_to_sat_uncert_km": None,
            "range_rate_sat_km_s": None,
            "range_rate_sat_uncert_km_s": None,
            "comments": None,
            "data_archive_link": None,
            "mpc_code": None,
        }
    ]

    result = process_upload_api(
        observations_data,
        timezone.now().isoformat(),
        "test@example.com",
        False,
    )

    # Observation should be created
    assert result["status"] == "SUCCESS"
    assert result["summary"]["total"] == 1
    assert result["summary"]["created"] == 1

    # Duplicated observation
    result = process_upload_api(
        observations_data,
        timezone.now().isoformat(),
        "test@example.com",
        False,
    )

    # No errors, but no new observation should be created
    assert result["status"] == "SUCCESS"
    assert result["summary"]["created"] == 0
    assert result["summary"]["duplicates"] == 1


@pytest.mark.django_db
def test_process_upload_api_rejected_task(mocker):
    """Test that task completes with a rejected observation"""
    # Mock all the things
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    mocker.patch("repository.tasks.send_confirmation_email")
    mocker.patch.object(process_upload_api, "update_state")

    # Mock the SatChecker response to return an error message
    mocker.patch(
        "repository.tasks.add_additional_data",
        return_value="Satellite below horizon at this time and location",
    )

    obs_time = timezone.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Rejected observation
    observations_data = [
        {
            "satellite_name": "TEST SAT",
            "satellite_number": 12345,
            "obs_time_utc": obs_time,
            "obs_time_uncert_sec": 0.1,
            "instrument": "TEST-SCOPE",
            "obs_mode": "CCD",
            "obs_filter": "Clear",
            "obs_email": "test@example.com",
            "obs_orc_id": ["0000-0000-0000-0000"],
            "obs_lat_deg": 20.0,
            "obs_long_deg": -155.0,
            "obs_alt_m": 3000.0,
            "limiting_magnitude": 18.0,
            "apparent_mag": 6,
            "apparent_mag_uncert": 1,
            "sat_ra_deg": None,
            "sat_dec_deg": None,
            "sigma_2_ra": None,
            "sigma_2_dec": None,
            "sigma_ra_sigma_dec": None,
            "range_to_sat_km": None,
            "range_to_sat_uncert_km": None,
            "range_rate_sat_km_s": None,
            "range_rate_sat_uncert_km_s": None,
            "comments": None,
            "data_archive_link": None,
            "mpc_code": None,
        }
    ]

    result = process_upload_api(
        observations_data,
        timezone.now().isoformat(),
        "test@example.com",
        False,
    )

    # Observation should be rejected
    assert result["status"] == "PARTIAL_SUCCESS"
    assert result["summary"]["total"] == 1
    assert result["summary"]["rejected"] == 1
    assert result["rejected_obs"][0] == {
        "index": 0,
        "sat_name": "TEST SAT",
        "sat_number": 12345,
        "obs_time_utc": "2024-01-01T00:00:00+00:00",
        "error": "Satellite below horizon at this time and location",
    }


@pytest.mark.django_db
def test_process_upload_api_null_email_task(mocker):
    """Test that the task uses the email from the first observation
    if no notification email is provided"""
    # Mock all the things
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    mock_send_confirmation_email = mocker.patch(
        "repository.tasks.send_confirmation_email"
    )
    mocker.patch.object(process_upload_api, "update_state")

    # Mock the SatChecker response
    mock_satchecker = mocker.Mock()
    mock_satchecker.alt_deg = 15.0
    mock_satchecker.illuminated = True
    mock_satchecker.phase_angle = 15.0
    mock_satchecker.range_to_sat = 500.0
    mock_satchecker.range_rate = 0.1
    mock_satchecker.sat_ra_deg = 180.0
    mock_satchecker.sat_dec_deg = 45.0
    mock_satchecker.ddec_deg_s = 0.01
    mock_satchecker.dra_cosdec_deg_s = 0.02
    mock_satchecker.az_deg = 270.0
    mock_satchecker.satellite_name = "TEST SAT"
    mock_satchecker.intl_designator = "2024-001A"
    mock_satchecker.sat_altitude_km = 400.0
    mock_satchecker.solar_elevation_deg = -10.0
    mock_satchecker.solar_azimuth_deg = 180.0
    mocker.patch("repository.tasks.add_additional_data", return_value=mock_satchecker)

    obs_time = timezone.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Completed, with accepted observation
    observations_data = [
        {
            "satellite_name": "TEST SAT",
            "satellite_number": 12345,
            "obs_time_utc": obs_time,
            "obs_time_uncert_sec": 0.1,
            "instrument": "TEST-SCOPE",
            "obs_mode": "CCD",
            "obs_filter": "Clear",
            "obs_email": "test123@example.com",
            "obs_orc_id": ["0000-0000-0000-0000"],
            "obs_lat_deg": 20.0,
            "obs_long_deg": -155.0,
            "obs_alt_m": 3000.0,
            "limiting_magnitude": 18.0,
            "apparent_mag": 6,
            "apparent_mag_uncert": 1,
            "sat_ra_deg": None,
            "sat_dec_deg": None,
            "sigma_2_ra": None,
            "sigma_2_dec": None,
            "sigma_ra_sigma_dec": None,
            "range_to_sat_km": None,
            "range_to_sat_uncert_km": None,
            "range_rate_sat_km_s": None,
            "range_rate_sat_uncert_km_s": None,
            "comments": None,
            "data_archive_link": None,
            "mpc_code": None,
        }
    ]

    result = process_upload_api(
        observations_data,
        timezone.now().isoformat(),
        None,  # no notification email specified
        True,  # send confirmation email
    )

    assert result["status"] == "SUCCESS"
    assert result["summary"]["total"] == 1
    assert mock_send_confirmation_email.call_args[0][1] == "test123@example.com"


@pytest.mark.django_db
def test_process_upload_api_magnitude_task(mocker):
    """
    Test that when apparent magnitude is provided but uncertainty is not,
    the observation is rejected
    """
    # Mock all the things
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    mocker.patch("repository.tasks.send_confirmation_email")
    mocker.patch.object(process_upload_api, "update_state")

    # Mock the SatChecker response
    mock_satchecker = mocker.Mock()
    mock_satchecker.alt_deg = 15.0
    mock_satchecker.illuminated = True
    mock_satchecker.phase_angle = 15.0
    mock_satchecker.range_to_sat = 500.0
    mock_satchecker.range_rate = 0.1
    mock_satchecker.sat_ra_deg = 180.0
    mock_satchecker.sat_dec_deg = 45.0
    mock_satchecker.ddec_deg_s = 0.01
    mock_satchecker.dra_cosdec_deg_s = 0.02
    mock_satchecker.az_deg = 270.0
    mock_satchecker.satellite_name = "TEST SAT"
    mock_satchecker.intl_designator = "2024-001A"
    mock_satchecker.sat_altitude_km = 400.0
    mock_satchecker.solar_elevation_deg = -10.0
    mock_satchecker.solar_azimuth_deg = 180.0
    mocker.patch("repository.tasks.add_additional_data", return_value=mock_satchecker)

    obs_time = timezone.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Completed, with accepted observation
    observations_data = [
        {
            "satellite_name": "TEST SAT",
            "satellite_number": 12345,
            "obs_time_utc": obs_time,
            "obs_time_uncert_sec": 0.1,
            "instrument": "TEST-SCOPE",
            "obs_mode": "CCD",
            "obs_filter": "Clear",
            "obs_email": "test@example.com",
            "obs_orc_id": ["0000-0000-0000-0000"],
            "obs_lat_deg": 20.0,
            "obs_long_deg": -155.0,
            "obs_alt_m": 3000.0,
            "limiting_magnitude": 18.0,
            "apparent_mag": 6,
            "apparent_mag_uncert": None,
            "sat_ra_deg": None,
            "sat_dec_deg": None,
            "sigma_2_ra": None,
            "sigma_2_dec": None,
            "sigma_ra_sigma_dec": None,
            "range_to_sat_km": None,
            "range_to_sat_uncert_km": None,
            "range_rate_sat_km_s": None,
            "range_rate_sat_uncert_km_s": None,
            "comments": None,
            "data_archive_link": None,
            "mpc_code": None,
        },
        {
            "satellite_name": "TEST SAT",
            "satellite_number": 12345,
            "obs_time_utc": obs_time,
            "obs_time_uncert_sec": 0.1,
            "instrument": "TEST-SCOPE",
            "obs_mode": "CCD",
            "obs_filter": "Clear",
            "obs_email": "test@example.com",
            "obs_orc_id": ["0000-0000-0000-0000"],
            "obs_lat_deg": 20.0,
            "obs_long_deg": -155.0,
            "obs_alt_m": 3000.0,
            "limiting_magnitude": 18.0,
            "apparent_mag": None,
            "apparent_mag_uncert": None,
            "sat_ra_deg": None,
            "sat_dec_deg": None,
            "sigma_2_ra": None,
            "sigma_2_dec": None,
            "sigma_ra_sigma_dec": None,
            "range_to_sat_km": None,
            "range_to_sat_uncert_km": None,
            "range_rate_sat_km_s": None,
            "range_rate_sat_uncert_km_s": None,
            "comments": None,
            "data_archive_link": None,
            "mpc_code": None,
        },
    ]

    result = process_upload_api(
        observations_data,
        timezone.now().isoformat(),
        None,
        False,
    )

    assert result["status"] == "PARTIAL_SUCCESS"
    assert result["summary"]["total"] == 2
    assert result["summary"]["created"] == 1
    assert result["summary"]["rejected"] == 1
    assert result["rejected_obs"][0] == {
        "index": 0,
        "sat_name": "TEST SAT",
        "sat_number": 12345,
        "obs_time_utc": "2024-01-01T00:00:00+00:00",
        "error": "Apparent magnitude uncertainty without apparent magnitude.",
    }


@pytest.mark.django_db
def test_process_upload_api_progress_task(mocker):
    """
    Test that progress updates are called correctly when processing multiple
    observations via the API upload task.
    """
    # Mock all the things
    mocker.patch("celery_progress.backend.ProgressRecorder.set_progress")
    mocker.patch("repository.tasks.send_confirmation_email")
    mocker.patch.object(process_upload_api, "update_state")

    obs_time = timezone.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Mock the SatChecker response
    mock_satchecker = mocker.Mock()
    mock_satchecker.alt_deg = 15.0
    mock_satchecker.illuminated = True
    mock_satchecker.phase_angle = 15.0
    mock_satchecker.range_to_sat = 500.0
    mock_satchecker.range_rate = 0.1
    mock_satchecker.sat_ra_deg = 180.0
    mock_satchecker.sat_dec_deg = 45.0
    mock_satchecker.ddec_deg_s = 0.01
    mock_satchecker.dra_cosdec_deg_s = 0.02
    mock_satchecker.az_deg = 270.0
    mock_satchecker.satellite_name = "TEST SAT"
    mock_satchecker.intl_designator = "2024-001A"
    mock_satchecker.sat_altitude_km = 400.0
    mock_satchecker.solar_elevation_deg = -10.0
    mock_satchecker.solar_azimuth_deg = 180.0
    mocker.patch("repository.tasks.add_additional_data", return_value=mock_satchecker)

    obs_time = timezone.datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    single_observation = {
        "satellite_name": "TEST SAT",
        "satellite_number": 12345,
        "obs_time_utc": obs_time,
        "obs_time_uncert_sec": 0.1,
        "instrument": "TEST-SCOPE",
        "obs_mode": "CCD",
        "obs_filter": "Clear",
        "obs_email": "test@example.com",
        "obs_orc_id": ["0000-0000-0000-0000"],
        "obs_lat_deg": 20.0,
        "obs_long_deg": -155.0,
        "obs_alt_m": 3000.0,
        "limiting_magnitude": 18.0,
        "apparent_mag": 6.0,
        "apparent_mag_uncert": 0.1,
        "sat_ra_deg": None,
        "sat_dec_deg": None,
        "sigma_2_ra": None,
        "sigma_2_dec": None,
        "sigma_ra_sigma_dec": None,
        "range_to_sat_km": None,
        "range_to_sat_uncert_km": None,
        "range_rate_sat_km_s": None,
        "range_rate_sat_uncert_km_s": None,
        "comments": None,
        "data_archive_link": None,
        "mpc_code": None,
    }

    # Create 10 identical observations
    observations_data = [single_observation.copy() for _ in range(10)]

    result = process_upload_api(
        observations_data,
        timezone.now().isoformat(),
        None,
        False,
    )

    # Check that update_state was called with progress updates
    assert result["status"] == "SUCCESS"
    assert result["summary"]["total"] == 10
    assert result["summary"]["created"] == 1
    assert result["summary"]["duplicates"] == 9
    assert result["summary"]["rejected"] == 0

    update_state_mock = process_upload_api.update_state
    assert update_state_mock.call_count == 11

    first_call = update_state_mock.call_args_list[0]
    assert first_call.kwargs["state"] == "PROGRESS"
    assert first_call.kwargs["meta"]["current"] == 0
    assert first_call.kwargs["meta"]["total"] == 10
    assert first_call.kwargs["meta"]["percent"] == 0
    assert "created_at" in first_call.kwargs["meta"]

    for i in range(1, 11):
        call = update_state_mock.call_args_list[i]
        assert call.kwargs["state"] == "PROGRESS"
        assert call.kwargs["meta"]["current"] == i
        assert call.kwargs["meta"]["total"] == 10
        assert call.kwargs["meta"]["percent"] == int((i / 10) * 100)
        assert call.kwargs["meta"]["description"] == f"Processing observation {i}/10"
        assert "created_at" in call.kwargs["meta"]

    last_call = update_state_mock.call_args_list[-1]
    assert last_call.kwargs["meta"]["percent"] == 100
    assert last_call.kwargs["meta"]["current"] == 10
    assert last_call.kwargs["meta"]["total"] == 10
