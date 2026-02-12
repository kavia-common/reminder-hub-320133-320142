import os
from typing import List

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import try_connect
from src.api.models import (
    ErrorResponse,
    Reminder,
    ReminderCreate,
    ReminderToggleComplete,
    ReminderUpdate,
)
from src.api.repository import (
    create_reminder,
    delete_reminder,
    get_reminder,
    list_reminders,
    set_completed,
    update_reminder,
)

openapi_tags = [
    {
        "name": "Health",
        "description": "Service health and diagnostics endpoints.",
    },
    {
        "name": "Reminders",
        "description": "CRUD operations for reminders and completion status.",
    },
]


def _parse_csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [v.strip() for v in raw.split(",") if v.strip()]


app = FastAPI(
    title="Reminders API",
    description=(
        "Backend API for the Reminders app. Provides CRUD endpoints for reminders "
        "including completion toggling."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# CORS: Align with frontend by allowing configured origins/methods/headers.
allowed_origins = _parse_csv_env("ALLOWED_ORIGINS", "*")
allowed_methods = _parse_csv_env("ALLOWED_METHODS", "GET,POST,PUT,DELETE,PATCH,OPTIONS")
allowed_headers = _parse_csv_env("ALLOWED_HEADERS", "*")
cors_max_age = int(os.getenv("CORS_MAX_AGE", "3600"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=allowed_methods if allowed_methods != ["*"] else ["*"],
    allow_headers=allowed_headers if allowed_headers != ["*"] else ["*"],
    max_age=cors_max_age,
)


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Simple liveness probe for the backend service.",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/health/db",
    tags=["Health"],
    summary="Database connectivity check",
    description=(
        "Checks whether the API can connect to Postgres. "
        "Requires DATABASE_URL (preferred) or POSTGRES_URL to be configured."
    ),
    responses={
        200: {"description": "Database reachable."},
        503: {"model": ErrorResponse, "description": "Database not reachable."},
    },
)
def db_health_check():
    """Return DB connectivity status."""
    err = try_connect()
    if err is not None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not reachable: {err}",
        )
    return {"ok": True}


# PUBLIC_INTERFACE
@app.get(
    "/reminders",
    tags=["Reminders"],
    summary="List reminders",
    description=(
        "Returns reminders ordered by due date ascending. "
        "Use include_completed=false to hide completed items."
    ),
    response_model=List[Reminder],
)
def api_list_reminders(
    include_completed: bool = Query(
        default=True, description="If false, only incomplete reminders are returned."
    ),
    limit: int = Query(
        default=200, ge=1, le=500, description="Max number of reminders to return."
    ),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
):
    """List reminders."""
    try:
        return list_reminders(
            include_completed=include_completed, limit=limit, offset=offset
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to list reminders: {exc}")


# PUBLIC_INTERFACE
@app.post(
    "/reminders",
    tags=["Reminders"],
    summary="Create a reminder",
    description="Creates a new reminder.",
    response_model=Reminder,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Reminder created."},
        500: {"model": ErrorResponse, "description": "Server error."},
    },
)
def api_create_reminder(payload: ReminderCreate):
    """Create a reminder."""
    try:
        return create_reminder(
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            notification_at=payload.notification_at,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to create reminder: {exc}")


# PUBLIC_INTERFACE
@app.get(
    "/reminders/{reminder_id}",
    tags=["Reminders"],
    summary="Get a reminder",
    description="Fetch a single reminder by id.",
    response_model=Reminder,
    responses={
        404: {"model": ErrorResponse, "description": "Reminder not found."},
        500: {"model": ErrorResponse, "description": "Server error."},
    },
)
def api_get_reminder(reminder_id: int):
    """Get one reminder by ID."""
    try:
        reminder = get_reminder(reminder_id)
        if reminder is None:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        return reminder
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to fetch reminder: {exc}")


# PUBLIC_INTERFACE
@app.put(
    "/reminders/{reminder_id}",
    tags=["Reminders"],
    summary="Update a reminder",
    description="Updates reminder fields (PUT semantics, but accepts partial fields).",
    response_model=Reminder,
    responses={
        404: {"model": ErrorResponse, "description": "Reminder not found."},
        500: {"model": ErrorResponse, "description": "Server error."},
    },
)
def api_update_reminder(reminder_id: int, payload: ReminderUpdate):
    """Update reminder by ID."""
    try:
        updated = update_reminder(
            reminder_id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            notification_at=payload.notification_at,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        return updated
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to update reminder: {exc}")


# PUBLIC_INTERFACE
@app.patch(
    "/reminders/{reminder_id}/completed",
    tags=["Reminders"],
    summary="Set reminder completion",
    description="Toggles (sets) a reminder's completed status.",
    response_model=Reminder,
    responses={
        404: {"model": ErrorResponse, "description": "Reminder not found."},
        500: {"model": ErrorResponse, "description": "Server error."},
    },
)
def api_set_completed(reminder_id: int, payload: ReminderToggleComplete):
    """Set completion status for a reminder."""
    try:
        updated = set_completed(reminder_id, completed=payload.completed)
        if updated is None:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        return updated
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle completion: {exc}"
        )


# PUBLIC_INTERFACE
@app.delete(
    "/reminders/{reminder_id}",
    tags=["Reminders"],
    summary="Delete a reminder",
    description="Deletes a reminder by id.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Reminder deleted."},
        404: {"model": ErrorResponse, "description": "Reminder not found."},
        500: {"model": ErrorResponse, "description": "Server error."},
    },
)
def api_delete_reminder(reminder_id: int) -> Response:
    """Delete reminder by ID."""
    try:
        deleted = delete_reminder(reminder_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to delete reminder: {exc}")
