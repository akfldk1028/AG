# api/routes/sessions.py
import json
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import text

from ...datamodel import Message, Response, Run, Session
from ..deps import get_db

router = APIRouter()


@router.get("/")
async def list_sessions(user_id: str, db=Depends(get_db)) -> Dict:
    """List all sessions for a user"""
    response = db.get(Session, filters={"user_id": user_id})
    return {"status": True, "data": response.data}


@router.get("/{session_id}")
async def get_session(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Get a specific session"""
    response = db.get(Session, filters={"id": session_id, "user_id": user_id})
    if not response.status or not response.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": True, "data": response.data[0]}


@router.post("/")
async def create_session(session: Session, db=Depends(get_db)) -> Response:
    """Create a new session"""
    try:
        response = db.upsert(session)
        if not response.status:
            return Response(status=False, message=f"Failed to create session: {response.message}")
        return Response(status=True, data=response.data, message="Session created successfully")
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return Response(status=False, message=f"Failed to create session: {str(e)}")


@router.put("/{session_id}")
async def update_session(session_id: int, user_id: str, session: Session, db=Depends(get_db)) -> Dict:
    """Update an existing session"""
    # First verify the session belongs to user
    existing = db.get(Session, filters={"id": session_id, "user_id": user_id})
    if not existing.status or not existing.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update the session
    response = db.upsert(session)
    if not response.status:
        raise HTTPException(status_code=400, detail=response.message)

    return {"status": True, "data": response.data, "message": "Session updated successfully"}


@router.delete("/{session_id}")
async def delete_session(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Delete a session"""
    db.delete(filters={"id": session_id, "user_id": user_id}, model_class=Session)
    return {"status": True, "message": "Session deleted successfully"}


@router.get("/{session_id}/runs")
async def list_session_runs(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Get complete session history organized by runs.

    Uses raw SQL to preserve the full JSON structure of team_result,
    including message content and type fields that would otherwise be
    lost during Pydantic deserialization of abstract base class unions.
    """
    from sqlmodel import Session as SQLSession

    try:
        # 1. Verify session exists and belongs to user
        session = db.get(Session, filters={"id": session_id, "user_id": user_id}, return_json=False)
        if not session.status:
            raise HTTPException(status_code=500, detail="Database error while fetching session")
        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        # 2. Get ordered runs for session using raw SQL to preserve JSON structure
        run_data = []
        with SQLSession(db.engine) as sql_session:
            runs_result = sql_session.execute(
                text("""
                    SELECT id, created_at, status, task, team_result
                    FROM run WHERE session_id = :session_id
                    ORDER BY created_at ASC
                """),
                {"session_id": session_id}
            ).fetchall()

            for run_row in runs_result:
                run_id = run_row[0]
                try:
                    # Get messages from Message table (these have correct type and content)
                    msg_result = sql_session.execute(
                        text("""
                            SELECT config FROM message
                            WHERE run_id = :run_id
                            ORDER BY created_at ASC
                        """),
                        {"run_id": run_id}
                    ).fetchall()

                    # Parse message configs
                    message_configs = []
                    for msg_row in msg_result:
                        if msg_row[0]:
                            msg_config = json.loads(msg_row[0]) if isinstance(msg_row[0], str) else msg_row[0]
                            message_configs.append(msg_config)

                    # Parse JSON fields that might be stored as strings
                    task_data = run_row[3]
                    if isinstance(task_data, str):
                        task_data = json.loads(task_data)

                    team_result_data = run_row[4]
                    if isinstance(team_result_data, str):
                        team_result_data = json.loads(team_result_data)

                    # Replace corrupted messages with correct Message table data
                    if team_result_data and isinstance(team_result_data, dict):
                        task_result = team_result_data.get('task_result')
                        if task_result and isinstance(task_result, dict) and message_configs:
                            task_result['messages'] = message_configs

                    run_data.append(
                        {
                            "id": str(run_id),
                            "created_at": run_row[1].isoformat() if run_row[1] and hasattr(run_row[1], 'isoformat') else (run_row[1] if run_row[1] else None),
                            "status": run_row[2],
                            "task": task_data,
                            "team_result": team_result_data,
                            "messages": message_configs,
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing run {run_id}: {str(e)}")
                    # Include run with error state instead of failing entirely
                    run_data.append(
                        {
                            "id": str(run_id),
                            "created_at": run_row[1].isoformat() if run_row[1] and hasattr(run_row[1], 'isoformat') else (run_row[1] if run_row[1] else None),
                            "status": "ERROR",
                            "task": None,
                            "team_result": None,
                            "messages": [],
                            "error": f"Failed to process run: {str(e)}",
                        }
                    )

        return {"status": True, "data": {"runs": run_data}}

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error in list_messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching session data") from e
