from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai_helper, schemas
from ..database import get_db

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


@router.post("/chat", response_model=schemas.AIChatResponse)
def ai_chat(chat_data: schemas.AIChatRequest, db: Session = Depends(get_db)):
    try:
        return ai_helper.generate_ai_response(
            db=db,
            message=chat_data.message,
            chat_history=[msg.model_dump() for msg in chat_data.chat_history]
        )
    except ai_helper.AIDisabledError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        # Without this, the clause below would relabel any deliberate 4xx/503
        # raised upstream as a 500 — HTTPException is itself an Exception.
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
