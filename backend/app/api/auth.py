from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from ..core import database, security
from ..models import User
from ..schemas import UserRegister, UserLogin, UserResponse, TokenWithUser

router = APIRouter()


@router.post("/register", response_model=TokenWithUser)
def register(user_data: UserRegister, db: Session = Depends(database.get_db)):
    if len(user_data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    user = User(
        email=user_data.email,
        password_hash=security.get_password_hash(user_data.password),
        email_confirmed_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = security.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.post("/login", response_model=TokenWithUser)
def login(user_data: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not security.verify_password(user_data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    token = security.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(security.get_current_user)):
    return current_user