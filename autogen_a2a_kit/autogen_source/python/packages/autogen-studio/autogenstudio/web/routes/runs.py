# /api/runs routes
import json
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from ...datamodel import Message, Run, RunStatus, Session
from ..deps import get_db

router = APIRouter()


class CreateRunRequest(BaseModel):
    session_id: int
    user_id: str


@router.post("/")
async def create_run(
    request: CreateRunRequest,
    db=Depends(get_db),
) -> Dict:
    """Create a new run with initial state"""
    session_response = db.get(
        Session, filters={"id": request.session_id, "user_id": request.user_id}, return_json=False
    )
    if not session_response.status or not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Create run with default state
        run = db.upsert(
            Run(
                session_id=request.session_id,
                status=RunStatus.CREATED,
                user_id=request.user_id,
                task={},  # Will be set when run starts
                team_result={},
            ),
            return_json=False,
        )
        return {"status": run.status, "data": {"run_id": run.data.id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# We might want to add these endpoints:


@router.get("/{run_id}")
async def get_run(run_id: int, db=Depends(get_db)) -> Dict:
    """Get run details including task and result.

    Uses raw SQL to preserve the full JSON structure.
    Also fetches messages from Message table as fallback since
    team_result.task_result.messages may be corrupted during serialization.
    """
    from sqlmodel import Session as SQLSession

    with SQLSession(db.engine) as session:
        # Get run data
        result = session.execute(
            text("""
                SELECT id, created_at, updated_at, user_id, version,
                       session_id, status, task, team_result, error_message, messages
                FROM run WHERE id = :run_id
            """),
            {"run_id": run_id}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Run not found")

        # Parse JSON fields
        team_result = json.loads(result[8]) if isinstance(result[8], str) else result[8]

        # Get messages from Message table (these have correct type and content)
        msg_result = session.execute(
            text("""
                SELECT config FROM message
                WHERE run_id = :run_id
                ORDER BY created_at ASC
            """),
            {"run_id": run_id}
        ).fetchall()

        # Parse message configs
        message_configs = []
        for row in msg_result:
            if row[0]:
                msg_config = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                message_configs.append(msg_config)

        # If team_result exists and has task_result, use Message table data as messages
        # This fixes the issue where team_result.task_result.messages loses type/content
        if team_result and isinstance(team_result, dict):
            task_result = team_result.get('task_result')
            if task_result and isinstance(task_result, dict):
                # Replace corrupted messages with correct Message table data
                if message_configs:
                    task_result['messages'] = message_configs

        # Build response
        run_data = {
            "id": result[0],
            "created_at": result[1].isoformat() if result[1] else None,
            "updated_at": result[2].isoformat() if result[2] else None,
            "user_id": result[3],
            "version": result[4],
            "session_id": result[5],
            "status": result[6],
            "task": json.loads(result[7]) if isinstance(result[7], str) else result[7],
            "team_result": team_result,
            "error_message": result[9],
            "messages": json.loads(result[10]) if isinstance(result[10], str) else result[10],
        }

        return {"status": True, "data": run_data}


@router.get("/{run_id}/messages")
async def get_run_messages(run_id: int, db=Depends(get_db)) -> Dict:
    """Get all messages for a run"""
    messages = db.get(Message, filters={"run_id": run_id}, order="asc", return_json=False)

    return {"status": True, "data": messages.data}
