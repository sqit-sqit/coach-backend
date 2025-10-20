# app/modules/spiral/chat_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.spiral.schemas import SpiralChatRequest, SpiralChatMessage
from app.modules.spiral.service_chat_simple import chat_with_spiral_ai, stream_chat_with_spiral_ai, get_or_create_spiral_session, save_chat_message
from app.modules.spiral.models import SpiralSession
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["spiral chat"])

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    lang: str | None = None

class ChatInitRequest(BaseModel):
    session_id: str
    lang: str | None = None

@router.post("/")
async def init_spiral_chat(
    request: ChatInitRequest,
    db: Session = Depends(get_db)
):
    """Initialize a spiral chat session and get the initial AI message."""
    try:
        # Ensure the spiral session exists
        spiral_session = db.query(SpiralSession).filter(SpiralSession.session_id == request.session_id).first()
        if not spiral_session:
            raise HTTPException(status_code=404, detail="Spiral session not found")

        # Generate the initial AI message using simple service
        initial_ai_message_content = chat_with_spiral_ai(
            user_message="",  # Empty message triggers initial response
            history=[],
            initial_problem=spiral_session.initial_problem,
            current_cycle=spiral_session.current_cycle,
            user_id=spiral_session.user_id,
            lang=(request.lang or "pl")
        )
        
        # Save the initial AI message
        db_ai_message = save_chat_message(
            db=db,
            session_id=request.session_id,
            role="assistant",
            content=initial_ai_message_content
        )
        
        return {
            "chat_session_id": request.session_id,
            "message": initial_ai_message_content
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{session_id}/stream")
async def stream_spiral_chat(
    session_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Stream chat responses for a spiral session."""
    try:
        # Ensure the spiral session exists
        spiral_session = db.query(SpiralSession).filter(SpiralSession.session_id == session_id).first()
        if not spiral_session:
            raise HTTPException(status_code=404, detail="Spiral session not found")

        # Save user message first
        save_chat_message(
            db=db,
            session_id=session_id,
            role="user",
            content=request.message
        )

        # Stream AI response using simple service
        ai_generator = stream_chat_with_spiral_ai(
            user_message=request.message,
            history=request.history,
            initial_problem=spiral_session.initial_problem,
            current_cycle=spiral_session.current_cycle,
            user_id=spiral_session.user_id,
            lang=(request.lang or "pl")
        )

        # Wrap chunks as proper Server-Sent Events and disable buffering
        def sse_generator():
            full_response = ""
            for chunk in ai_generator:
                if chunk:
                    full_response += chunk
                    yield f"data: {chunk}\n\n"
            
            # Save the complete AI response
            if full_response:
                save_chat_message(
                    db=db,
                    session_id=session_id,
                    role="assistant",
                    content=full_response
                )

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }

        return StreamingResponse(sse_generator(), media_type="text/event-stream", headers=headers)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{session_id}/start", response_model=SpiralChatMessage)
async def start_spiral_chat(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Start a new spiral chat session and get the initial AI message."""
    try:
        # Ensure the spiral session exists
        spiral_session = db.query(SpiralSession).filter(SpiralSession.session_id == session_id).first()
        if not spiral_session:
            raise HTTPException(status_code=404, detail="Spiral session not found")

        # Generate the initial AI message using simple service
        initial_ai_message_content = chat_with_spiral_ai(
            user_message="",  # Empty message triggers initial response
            history=[],
            initial_problem=spiral_session.initial_problem,
            current_cycle=spiral_session.current_cycle,
            user_id=spiral_session.user_id
        )
        
        # Save the initial AI message
        db_ai_message = save_chat_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=initial_ai_message_content
        )
        
        return SpiralChatMessage(
            id=db_ai_message.id,
            session_id=db_ai_message.session_id,
            role=db_ai_message.role,
            content=db_ai_message.content,
            cycle_number=db_ai_message.cycle_number,
            question_type=db_ai_message.question_type,
            is_summary=db_ai_message.is_summary,
            has_action_chips=db_ai_message.has_action_chips,
            created_at=db_ai_message.created_at,
            message_order=db_ai_message.message_order
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")