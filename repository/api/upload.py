from uuid import UUID, uuid4

from celery.result import AsyncResult
from celery_progress.backend import Progress
from django.utils import timezone
from ninja import Router

from ..tasks import process_upload_api
from .schemas import (
    ErrorSchema,
    ObservationBatchUploadSchema,
    ProgressSchema,
    RejectedObservationSchema,
    SummarySchema,
    UploadCompletedSchema,
    UploadCompletedWithErrorSchema,
    UploadFailedSchema,
    UploadProgressSchema,
    UploadResponseSchema,
)

router = Router()


@router.post("", response=UploadResponseSchema)
def upload_observations(request, data: ObservationBatchUploadSchema):
    """Upload observations

    Upload an observation set to the database. This uses the same logic to validate
    observations as the file upload endpoint, but does not stop on failures -
    all rejected observations are added to the response with reasons for failure.

    The batch_id is optional and can be provided in the request body.
    If not provided, one will be generated automatically and returned in the response.

    If no notification email is provided, the email in the first observation
    will be used for confirmation email if one is requested.
    """

    # start Celery task to process the upload

    # Convert Pydantic schemas to dictionaries for Celery serialization
    observations_data = [obs.model_dump() for obs in data.observations]

    task_id = (
        str(data.batch_id) if data.batch_id else str(uuid4())
    )  # Celery requires string, not UUID object
    created_at = (
        timezone.now().isoformat()
    )  # Convert to string for Celery serialization
    upload_task = process_upload_api.apply_async(
        args=[
            observations_data,
            created_at,
            data.notification_email,
            data.send_confirmation,
        ],
        task_id=task_id,
    )

    response = UploadResponseSchema(
        batch_id=upload_task.task_id, status="PENDING", created_at=created_at
    )  # Client should store this

    return response


@router.get(
    "/{batch_id}/status",
    response={
        200: UploadCompletedWithErrorSchema
        | UploadCompletedSchema
        | UploadProgressSchema
        | UploadResponseSchema,
        500: UploadFailedSchema,
    },
)
def get_upload_status(request, batch_id: UUID):
    """Get the status of a batch upload

    Get the status of a batch upload. This is used to get the in-progress status of a
    batch upload, as well as the final status when the upload is complete.

    ### Parameters
    - **batch_id**: The ID of the batch upload
    """

    # Get the Celery task result
    task = AsyncResult(str(batch_id))

    progress_info = Progress(task).get_info()

    created_at = None
    if task.info and isinstance(task.info, dict):
        created_at = task.info.get("created_at")

    # Base response
    base_response = {
        "batch_id": batch_id,
        "created_at": created_at or timezone.now().isoformat(),
    }

    # Handle different task states
    if progress_info["state"] == "PENDING":
        # Task is queued but hasn't started yet
        return 200, UploadResponseSchema(**base_response, status="PENDING")

    elif progress_info["state"] == "PROGRESS":
        return 200, UploadProgressSchema(
            **base_response,
            status="PROCESSING",
            progress=ProgressSchema(
                total=progress_info.get("total", 0),
                processed=progress_info.get("current", 0),
                percent=progress_info.get("percent", 0),
            ),
        )

    elif progress_info["state"] == "SUCCESS":
        result = task.result

        # Check if there were any rejected observations
        if result and result.get("rejected_obs"):
            return 200, UploadCompletedWithErrorSchema(
                **base_response,
                status="PARTIAL_SUCCESS",
                summary=SummarySchema(**result["summary"]),
                rejected_obs=[
                    RejectedObservationSchema(**obs) for obs in result["rejected_obs"]
                ],
            )
        elif result and result.get("summary"):
            return 200, UploadCompletedSchema(
                **base_response,
                status="SUCCESS",
                summary=SummarySchema(**result["summary"]),
            )
        else:
            # is this needed?
            print(f"Falling back to basic response. Result was: {result}")
            return 200, UploadResponseSchema(**base_response, status="SUCCESS")

    elif progress_info["state"] == "FAILURE":
        error_msg = str(task.info) if task.info else "Unknown error occurred"
        return 500, UploadFailedSchema(
            **base_response,
            status="FAILED",
            error=ErrorSchema(message=error_msg, code=500),
        )

    else:
        # Handle other states (RETRY, REVOKED, etc.)
        return 200, UploadResponseSchema(**base_response, status=progress_info["state"])
