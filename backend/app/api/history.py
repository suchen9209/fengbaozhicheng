"""
API endpoint for history records
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.history_service import HistoryService

router = APIRouter()


@router.get("/api/v1/history")
async def get_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get analysis history records
    
    Args:
        limit: Maximum number of records to return (1-100, default: 20)
        offset: Number of records to skip (default: 0)
        session_id: Filter by session ID (optional)
        user_id: Filter by user ID (optional)
        db: Database session
    
    Returns:
        JSON response with history records
    """
    import uuid
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    history_service = HistoryService(db)
    
    # Get records
    records = history_service.get_records(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    # Get total count
    total = history_service.get_total_count(
        user_id=user_id,
        session_id=session_id
    )
    
    # Build response
    return {
        "request_id": request_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": [
            {
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "screenshot_url": f"/{record.screenshot_path}",
                "game_state": {
                    "available_blueprints": record.game_state.available_blueprints,
                    "resources": record.game_state.resources,
                    "species": record.game_state.species,
                    "confidence": record.game_state.confidence
                },
                "recommendations": [
                    {
                        "blueprint_name": rec.blueprint_name,
                        "score": rec.score,
                        "rank": rec.rank,
                        "reasoning": rec.reasoning
                    }
                    for rec in record.recommendations
                ]
            }
            for record in records
        ]
    }
