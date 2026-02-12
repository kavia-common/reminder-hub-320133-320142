from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg

from src.api.db import get_db_connection


def _row_to_reminder(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize DB row dict to API reminder dict."""
    # psycopg dict_row already yields keys matching columns.
    return {
        "id": int(row["id"]),
        "title": row["title"],
        "description": row["description"],
        "due_date": row["due_date"],
        "notification_at": row["notification_at"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_reminders(
    *, include_completed: bool = True, limit: int = 200, offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch reminders ordered by due_date ascending."""
    where = "" if include_completed else "WHERE completed = false"
    sql = f"""
        SELECT id, title, description, due_date, notification_at, completed, created_at, updated_at
        FROM public.reminders
        {where}
        ORDER BY due_date ASC, id ASC
        LIMIT %s OFFSET %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()
    return [_row_to_reminder(r) for r in rows]


def get_reminder(reminder_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single reminder by ID."""
    sql = """
        SELECT id, title, description, due_date, notification_at, completed, created_at, updated_at
        FROM public.reminders
        WHERE id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (reminder_id,))
            row = cur.fetchone()
    return _row_to_reminder(row) if row else None


def create_reminder(
    *,
    title: str,
    description: Optional[str],
    due_date: datetime,
    notification_at: Optional[datetime],
) -> Dict[str, Any]:
    """Insert a reminder and return the created row."""
    sql = """
        INSERT INTO public.reminders (title, description, due_date, notification_at, completed)
        VALUES (%s, %s, %s, %s, false)
        RETURNING id, title, description, due_date, notification_at, completed, created_at, updated_at;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (title, description, due_date, notification_at))
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise RuntimeError("Failed to create reminder.")
    return _row_to_reminder(row)


def _build_update_set_clause(
    updates: Dict[str, Any],
) -> Tuple[str, List[Any]]:
    """Build SET clause for partial update."""
    parts: List[str] = []
    values: List[Any] = []
    for col, value in updates.items():
        parts.append(f"{col} = %s")
        values.append(value)
    return ", ".join(parts), values


def update_reminder(
    reminder_id: int,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[datetime] = None,
    notification_at: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Patch reminder fields. Returns updated row, or None if not found."""
    updates: Dict[str, Any] = {}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if due_date is not None:
        updates["due_date"] = due_date
    if notification_at is not None:
        updates["notification_at"] = notification_at

    if not updates:
        # No-op update; still return existing reminder (or None).
        return get_reminder(reminder_id)

    set_clause, values = _build_update_set_clause(updates)
    sql = f"""
        UPDATE public.reminders
        SET {set_clause}
        WHERE id = %s
        RETURNING id, title, description, due_date, notification_at, completed, created_at, updated_at;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (*values, reminder_id))
            row = cur.fetchone()
        conn.commit()

    return _row_to_reminder(row) if row else None


def set_completed(reminder_id: int, *, completed: bool) -> Optional[Dict[str, Any]]:
    """Update completion status. Returns updated row, or None if not found."""
    sql = """
        UPDATE public.reminders
        SET completed = %s
        WHERE id = %s
        RETURNING id, title, description, due_date, notification_at, completed, created_at, updated_at;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (completed, reminder_id))
            row = cur.fetchone()
        conn.commit()
    return _row_to_reminder(row) if row else None


def delete_reminder(reminder_id: int) -> bool:
    """Delete reminder by ID. Returns True if deleted, False if missing."""
    sql = "DELETE FROM public.reminders WHERE id = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (reminder_id,))
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def is_foreign_key_violation(exc: Exception) -> bool:
    """Best-effort check for FK violation (not expected for this schema)."""
    if isinstance(exc, psycopg.errors.ForeignKeyViolation):
        return True
    return False
