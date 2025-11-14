from django.http import JsonResponse
from ninja import NinjaAPI
from ninja.errors import HttpError, ValidationError
from ninja.throttling import AnonRateThrottle

from .observations import router as observations_router
from .satellites import router as satellites_router
from .upload import router as upload_router


def validation_error_handler(request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors:
        # Create user-friendly error message

        # top level error
        if len(error["loc"]) == 3:
            error_detail = {
                "field": error["loc"][2],
                "message": error["msg"],
                "type": error["type"],
            }
        # field level error
        else:
            error_detail = {
                "observation_index": error["loc"][3],
                "field": error["loc"][4],
                "message": error["msg"],
                "type": error["type"],
            }

        if "input" in error:
            error_detail["received_value"] = error["input"]

        errors.append(error_detail)

    return JsonResponse(
        {
            "error": "Validation failed",
            "message": "One or more fields have invalid values or types",
            "details": errors,
        },
        status=422,
    )


def http_error_handler(request, exc: HttpError):
    """Handle HTTP errors"""
    return JsonResponse({"error": str(exc)}, status=exc.status_code)


api = NinjaAPI(
    title="SCORE API",
    description="API for accessing and uploadingsatellite observation data",
    version="2.0.0",
    throttle=[
        AnonRateThrottle("10/s"),
    ],
)

# Add custom error handlers
api.add_exception_handler(ValidationError, validation_error_handler)
api.add_exception_handler(HttpError, http_error_handler)

api.add_router("/observations", observations_router)
api.add_router("/satellites", satellites_router)
api.add_router("/upload", upload_router)
