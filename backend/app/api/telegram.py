from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta
from ..core import database, security
from ..models import User
from ..schemas import TelegramCodeResponse, TelegramVerifyRequest

router = APIRouter()

telegram_codes = {}


@router.post("/telegram/generate-code", response_model=TelegramCodeResponse)
def generate_telegram_code(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    code = secrets.randbelow(1000000)
    code_str = f"{code:06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    telegram_codes[code_str] = (current_user.id, expires_at)
    
    for key, (_, exp) in list(telegram_codes.items()):
        if exp < datetime.utcnow():
            del telegram_codes[key]
    
    return {"code": code_str, "expires_in": 900}


@router.post("/telegram/verify-code")
def verify_telegram_code(
    request: TelegramVerifyRequest,
    db: Session = Depends(database.get_db)
):
    if request.code not in telegram_codes:
        raise HTTPException(400, "Invalid or expired code")
    
    user_id, expires_at = telegram_codes[request.code]
    if expires_at < datetime.utcnow():
        del telegram_codes[request.code]
        raise HTTPException(400, "Code expired")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    existing = db.query(User).filter(User.telegram_id == request.telegram_id).first()
    if existing and existing.id != user.id:
        raise HTTPException(400, "Telegram account already linked to another user")
    
    user.telegram_id = request.telegram_id
    db.commit()
    del telegram_codes[request.code]
    return {"message": "Telegram account linked successfully"}