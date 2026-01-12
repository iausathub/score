from ninja.security import HttpBearer

from repository.models import APIKey


class APIKeyAuth(HttpBearer):
    """
    Extracts the API key from the Authorization header (Bearer token)
    and validates it against the APIKey model.
    """

    def authenticate(self, request, token):
        """
        Authenticate the request using the provided API key.

        Args:
            request: The HTTP request object
            token: The API key from the Authorization header

        Returns:
            APIKey object if authentication succeeds, None otherwise
        """
        api_key = APIKey.validate_key(token)

        if api_key is None:
            return None

        # Record usage
        api_key.record_usage()

        # Store the API key object in the request for later use
        request.api_key = api_key

        return api_key
