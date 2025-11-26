"""
Admin views for managing API keys and other administrative tasks.
These views require staff/superuser access.
"""

import logging
import re

import requests
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError
from django.shortcuts import redirect, render

from .models import APIKey

logger = logging.getLogger(__name__)


@staff_member_required
def create_api_key_view(request):
    """
    View for creating API keys through the web interface.
    Only accessible to users with staff permissions.
    """
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        orcid_id = request.POST.get("orcid_id")
        expires_in_days = request.POST.get("expires_in_days")
        notes = request.POST.get("notes", "")

        # Validation
        if not name or not email:
            messages.error(request, "Name and email are required.")
            return render(request, "repository/admin/create_api_key.html")

        # Verify ORCID ID
        try:
            orcid_error_message = "Invalid ORCID ID. Must be a valid ORCID ID."
            # Validate and sanitize the ORCID ID
            orcid_id = orcid_id.strip().upper()
            if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]$", orcid_id):
                messages.error(request, orcid_error_message)
                return render(request, "repository/admin/create_api_key.html")

            # Use Accept header to get XML response, which returns 404 for invalid
            # ORCID IDs - if using the regular request it returns 200 for everything.
            response = requests.get(
                f"https://orcid.org/{orcid_id}",
                headers={"Accept": "application/xml"},
                timeout=30,
            )
            if response.status_code != 200:
                messages.error(request, orcid_error_message)
                return render(request, "repository/admin/create_api_key.html")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            return render(request, "repository/admin/create_api_key.html")

        # Convert expires_in_days to int or None
        try:
            expires_in_days = int(expires_in_days) if expires_in_days else None
        except ValueError:
            messages.error(request, "Invalid expiration days. Must be a number.")
            return render(request, "repository/admin/create_api_key.html")

        try:
            # Create the API key
            api_key, plaintext_key = APIKey.create_key(
                name=name,
                email=email,
                orcid_id=orcid_id,
                expires_in_days=expires_in_days,
                notes=notes,
            )

            # Store the plaintext key in session to display on next page
            request.session["new_api_key"] = {
                "key": plaintext_key,
                "name": name,
                "email": email,
                "orcid_id": orcid_id,
                "prefix": api_key.key_prefix,
                "created_at": api_key.created_at.isoformat(),
                "expires_at": api_key.expires_at.isoformat()
                if api_key.expires_at
                else None,
            }

            # Set session to expire when browser closes for security
            request.session.set_expiry(0)

            return redirect("show_api_key")

        except (ValidationError, IntegrityError) as e:
            logger.error(f"Validation error creating API key: {e}")
            messages.error(request, f"Failed to create API key: {str(e)}")
            return render(request, "repository/admin/create_api_key.html")
        except DatabaseError as e:
            logger.error(f"Database error creating API key: {e}")
            messages.error(request, "Database error. Please try again.")
            return render(request, "repository/admin/create_api_key.html")
        except Exception as e:
            logger.exception(f"Unexpected error creating API key: {e}")
            messages.error(request, "An unexpected error occurred.")
            return render(request, "repository/admin/create_api_key.html")

    return render(request, "repository/admin/create_api_key.html")


@staff_member_required
def list_api_keys_view(request):
    """
    List all API keys with their status and usage information.
    """
    # Get filter parameters
    show_all = request.GET.get("show_all", "false") == "true"

    if show_all:
        api_keys = APIKey.objects.all().order_by("-created_at")
        title = "All API Keys"
    else:
        api_keys = APIKey.objects.filter(is_active=True).order_by("-created_at")
        title = "Active API Keys"

    context = {
        "api_keys": api_keys,
        "title": title,
        "show_all": show_all,
    }

    return render(request, "repository/admin/list_api_keys.html", context)


@staff_member_required
def revoke_api_key_view(request, key_id):
    """
    Revoke an API key.
    """
    try:
        api_key = APIKey.objects.get(id=key_id)

        if request.method == "POST":
            api_key.revoke()
            messages.success(
                request,
                f"API key for {api_key.name} ({api_key.email}) has been revoked.",
            )
            return redirect("list_api_keys")

        # Show confirmation page
        return render(
            request, "repository/admin/revoke_api_key.html", {"api_key": api_key}
        )

    except APIKey.DoesNotExist:
        messages.error(request, "API key not found.")
        return redirect("list_api_keys")
