"""Tests for the APIKey model and authentication."""

from datetime import timedelta

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from repository.models import APIKey, APIKeyVerification


@pytest.mark.django_db
def test_create_api_key():
    """Test creating an API key"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User",
        email="test@example.com",
        orcid_id="0000-0000-0000-0000",
        notes="Test key",
    )

    assert api_key is not None
    assert plaintext_key is not None
    assert len(plaintext_key) > 20
    assert api_key.name == "Test User"
    assert api_key.email == "test@example.com"
    assert api_key.orcid_id == "0000-0000-0000-0000"
    assert api_key.notes == "Test key"
    assert api_key.is_active is True
    assert api_key.usage_count == 0
    assert api_key.last_used_at is None


@pytest.mark.django_db
def test_create_api_key_with_expiration():
    """Test creating an API key with expiration"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User",
        email="test@example.com",
        orcid_id="0000-0000-0000-0000",
        expires_in_days=30,
    )

    assert api_key.expires_at is not None
    # Check that expiration is roughly 30 days from now
    expected_expiry = timezone.now() + timedelta(days=30)
    time_diff = abs((api_key.expires_at - expected_expiry).total_seconds())
    assert time_diff < 60


@pytest.mark.django_db
def test_validate_api_key():
    """Test validating a valid API key"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User", email="test@example.com", orcid_id="0000-0000-0000-0000"
    )

    # valid key
    validated_key = APIKey.validate_key(plaintext_key)
    assert validated_key is not None
    assert validated_key.id == api_key.id

    # invalid key
    validated_key = APIKey.validate_key("invalid_key_12345")
    assert validated_key is None


@pytest.mark.django_db
def test_validate_api_key_inactive():
    """Test validating an inactive API key"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User", email="test@example.com", orcid_id="0000-0000-0000-0000"
    )

    # Deactivate the key
    api_key.is_active = False
    api_key.save()

    validated_key = APIKey.validate_key(plaintext_key)
    assert validated_key is None


@pytest.mark.django_db
def test_validate_api_key_expired():
    """Test validating an expired API key"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User",
        email="test@example.com",
        orcid_id="0000-0000-0000-0000",
        expires_in_days=1,
    )

    # Manually set expiration to the past
    api_key.expires_at = timezone.now() - timedelta(days=1)
    api_key.save()

    validated_key = APIKey.validate_key(plaintext_key)
    assert validated_key is None


@pytest.mark.django_db
def test_record_usage():
    """Test recording API key usage"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User", email="test@example.com", orcid_id="0000-0000-0000-0000"
    )

    assert api_key.usage_count == 0
    assert api_key.last_used_at is None

    # Record usage
    api_key.record_usage()

    api_key.refresh_from_db()
    assert api_key.usage_count == 1
    assert api_key.last_used_at is not None

    # Record usage again
    api_key.record_usage()
    api_key.refresh_from_db()
    assert api_key.usage_count == 2


@pytest.mark.django_db
def test_revoke_api_key():
    """Test revoking an API key"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User", email="test@example.com", orcid_id="0000-0000-0000-0000"
    )

    assert api_key.is_active is True
    assert api_key.is_valid() is True

    # Revoke the key
    api_key.revoke()

    assert api_key.is_active is False
    assert api_key.is_valid() is False

    # Should not be able to validate after revocation
    validated_key = APIKey.validate_key(plaintext_key)
    assert validated_key is None


@pytest.mark.django_db
def test_is_valid():
    """Test the is_valid method"""
    # Active key with no expiration
    api_key1, _ = APIKey.create_key(
        name="User 1", email="user1@example.com", orcid_id="0000-0001-2345-6789"
    )
    assert api_key1.is_valid() is True

    # Active key with future expiration
    api_key2, _ = APIKey.create_key(
        name="User 2",
        email="user2@example.com",
        orcid_id="0000-0001-2345-6789",
        expires_in_days=30,
    )
    assert api_key2.is_valid() is True

    # Inactive key
    api_key3, _ = APIKey.create_key(
        name="User 3", email="user3@example.com", orcid_id="0000-0001-2345-6789"
    )
    api_key3.is_active = False
    api_key3.save()
    assert api_key3.is_valid() is False

    # Expired key
    api_key4, _ = APIKey.create_key(
        name="User 4",
        email="user4@example.com",
        orcid_id="0000-0001-2345-6789",
        expires_in_days=1,
    )
    api_key4.expires_at = timezone.now() - timedelta(days=1)
    api_key4.save()
    assert api_key4.is_valid() is False


@pytest.mark.django_db
def test_key_prefix():
    """Test that key prefix is correctly set"""
    api_key, plaintext_key = APIKey.create_key(
        name="Test User", email="test@example.com", orcid_id="0000-0000-0000-0000"
    )

    # Prefix should be first 8 characters of the plaintext key
    assert api_key.key_prefix == plaintext_key[:8]


@pytest.mark.django_db
def test_hash_key():
    """Test that keys are properly hashed"""
    plaintext_key = "test_key_12345"
    hashed = APIKey.hash_key(plaintext_key)

    assert APIKey.hash_key(plaintext_key) == hashed
    assert APIKey.hash_key("different_key") != hashed

    # Hash should be SHA-256 (64 hex characters)
    assert len(hashed) == 64


@pytest.fixture
def verification():
    """Create a test verification record."""
    return APIKeyVerification.objects.create(
        name="Test User",
        email="test@example.com",
        orcid_id="0000-0001-2345-6789",
        expires_at=timezone.now() + timedelta(minutes=30),
    )


@pytest.mark.django_db
def test_get_request_shows_form():
    """Test that GET request shows the API key request form."""
    client = Client()
    response = client.get(reverse("request-api-key"))

    assert response.status_code == 200
    assert b"Request API Key" in response.content


@pytest.mark.django_db
def test_valid_request_creates_verification(mocker, settings):
    """Test that valid POST creates verification and sends email."""
    settings.RATELIMIT_ENABLE = False
    client = Client()

    # Mock ORCID validation
    mock_requests = mocker.patch("repository.views.requests.get")
    mock_response = mock_requests.return_value
    mock_response.status_code = 200

    response = client.post(
        reverse("request-api-key"),
        {
            "name": "Test User",
            "email": "test@example.com",
            "orcid_id": "0000-0001-2345-6789",
        },
    )

    # Should redirect back to form with success message
    assert response.status_code == 200

    # Check verification was created
    verification = APIKeyVerification.objects.filter(email="test@example.com").first()
    assert verification is not None
    assert verification.name == "Test User"
    assert verification.orcid_id == "0000-0001-2345-6789"
    assert verification.is_active()

    # Check email was sent
    assert len(mail.outbox) == 1
    assert "verification" in mail.outbox[0].subject.lower()
    assert "test@example.com" in mail.outbox[0].to


@pytest.mark.django_db
def test_missing_fields_returns_error(settings):
    """Test that missing required fields returns error."""
    settings.RATELIMIT_ENABLE = False
    client = Client()
    response = client.post(
        reverse("request-api-key"),
        {
            "name": "Test User",
            # Missing email and orcid_id
        },
    )

    assert response.status_code == 200
    assert b"Invalid request" in response.content or b"required" in response.content


@pytest.mark.django_db
def test_invalid_orcid_format_returns_error(settings):
    """Test that invalid ORCID format is rejected."""
    settings.RATELIMIT_ENABLE = False
    client = Client()
    response = client.post(
        reverse("request-api-key"),
        {"name": "Test User", "email": "test@example.com", "orcid_id": "invalid-orcid"},
    )

    assert response.status_code == 200
    assert b"Invalid ORCID" in response.content


@pytest.mark.django_db
def test_nonexistent_orcid_returns_error(mocker, settings):
    """Test that non-existent ORCID is rejected."""
    settings.RATELIMIT_ENABLE = False
    client = Client()

    # Mock ORCID API returning 404
    mock_requests = mocker.patch("repository.views.requests.get")
    mock_response = mock_requests.return_value
    mock_response.status_code = 404

    response = client.post(
        reverse("request-api-key"),
        {
            "name": "Test User",
            "email": "test@example.com",
            "orcid_id": "0000-0001-2345-6789",
        },
    )

    assert response.status_code == 200
    assert b"Invalid ORCID" in response.content


@pytest.mark.django_db
def test_valid_token_creates_api_key(verification):
    """Test that valid token creates API key and shows it once."""
    client = Client()
    url = reverse("verify_email", kwargs={"token": verification.verification_token})
    response = client.get(url)

    # Should redirect to show API key page
    assert response.status_code == 302
    assert "show" in response.url

    # Follow redirect
    response = client.get(response.url)
    assert response.status_code == 200

    # Check API key was created
    api_key = APIKey.objects.filter(email="test@example.com").first()
    assert api_key is not None
    assert api_key.name == "Test User"
    assert api_key.orcid_id == "0000-0001-2345-6789"
    assert api_key.is_active

    # Verification should be deleted (single-use)
    assert not APIKeyVerification.objects.filter(
        verification_token=verification.verification_token
    ).exists()


@pytest.mark.django_db
def test_expired_token_returns_error(verification):
    """Test that expired token is rejected."""
    client = Client()

    # Set verification to expired
    verification.expires_at = timezone.now() - timedelta(minutes=1)
    verification.save()

    url = reverse("verify_email", kwargs={"token": verification.verification_token})
    response = client.get(url)

    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"failed" in content_lower or b"expired" in content_lower

    # No API key should be created
    assert not APIKey.objects.filter(email="test@example.com").exists()


@pytest.mark.django_db
def test_invalid_token_returns_error():
    """Test that invalid token is rejected."""
    import uuid

    client = Client()
    fake_token = uuid.uuid4()

    url = reverse("verify_email", kwargs={"token": fake_token})
    response = client.get(url)

    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"failed" in content_lower or b"expired" in content_lower


@pytest.mark.django_db
def test_reusing_token_fails(verification):
    """Test that token can only be used once."""
    client = Client()
    url = reverse("verify_email", kwargs={"token": verification.verification_token})

    # First use - should work
    response = client.get(url)
    assert response.status_code == 302

    # Second use - should fail (token deleted)
    response = client.get(url)
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"failed" in content_lower or b"expired" in content_lower


@pytest.mark.django_db
def test_rate_limiting(mocker, settings):
    """Test that rate limiting is enforced and returns 429 status code.
    The django-ratelimit library returns a 403 status code by default"""
    settings.RATELIMIT_ENABLE = True

    client = Client()

    # Mock ORCID validation
    mock_requests = mocker.patch("repository.views.requests.get")
    mock_response = mock_requests.return_value
    mock_response.status_code = 200

    # Rate limit is 3/h per IP and per email
    # Make 4 requests with the same email to trigger rate limiting
    for i in range(4):
        response = client.post(
            reverse("request-api-key"),
            {
                "name": "Test User",
                "email": "test@example.com",  # Same email for all requests
                "orcid_id": "0000-0001-2345-6789",
            },
        )

        if i < 3:
            # First 3 should succeed
            assert response.status_code == 200
        else:
            # 4th should be rate limited with 429 status
            assert response.status_code == 429
            assert b"Too many requests" in response.content


@pytest.mark.django_db
def test_complete_flow(mocker, settings):
    """Test the complete flow from request to key creation."""
    settings.RATELIMIT_ENABLE = False
    client = Client()

    # Mock ORCID validation
    mock_requests = mocker.patch("repository.views.requests.get")
    mock_response = mock_requests.return_value
    mock_response.status_code = 200

    # Step 1: Request API key
    response = client.post(
        reverse("request-api-key"),
        {
            "name": "Integration Test User",
            "email": "integration@example.com",
            "orcid_id": "0000-0001-2345-6789",
        },
    )

    assert response.status_code == 200

    # Verify email was sent
    assert len(mail.outbox) == 1

    # Step 2: Get verification token from database
    verification = APIKeyVerification.objects.get(email="integration@example.com")

    # Step 3: Verify email (click link)
    verify_url = reverse(
        "verify_email", kwargs={"token": verification.verification_token}
    )
    response = client.get(verify_url)

    # Should redirect to show key page
    assert response.status_code == 302

    # Step 4: Check API key was created
    api_key = APIKey.objects.get(email="integration@example.com")
    assert api_key.name == "Integration Test User"
    assert api_key.orcid_id == "0000-0001-2345-6789"
    assert api_key.is_active
    assert api_key.expires_at is not None  # Should expire in 90 days

    # Step 5: Verification should be deleted
    assert not APIKeyVerification.objects.filter(
        email="integration@example.com"
    ).exists()
