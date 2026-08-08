from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai_helper, schemas
from ..database import get_db

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


@router.post("/chat", response_model=schemas.AIChatResponse)
def ai_chat(chat_data: schemas.AIChatRequest, db: Session = Depends(get_db)):
    try:
        response_dict = ai_helper.generate_ai_response(
            db=db,
            message=chat_data.message,
            chat_history=[msg.model_dump() for msg in chat_data.chat_history]
        )
        return response_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
