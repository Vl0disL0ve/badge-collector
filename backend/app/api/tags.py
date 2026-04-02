from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..core import database, security
from ..models import User, Tag
from ..schemas import TagCreate, TagUpdate, TagResponse

router = APIRouter()


@router.get("/tags", response_model=List[TagResponse])
def get_tags(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    tags = db.query(Tag).filter(Tag.user_id == current_user.id).all()
    return [TagResponse(id=t.id, name=t.name, user_id=t.user_id, created_at=t.created_at) for t in tags]


@router.put("/tags/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    tag = db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.user_id == current_user.id
    ).first()
    if not tag:
        raise HTTPException(404, "Tag not found")
    
    if data.name is not None:
        tag.name = data.name.lower()
    
    db.commit()
    db.refresh(tag)
    
    return TagResponse(id=tag.id, name=tag.name, user_id=tag.user_id, created_at=tag.created_at)


@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    tag = db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.user_id == current_user.id
    ).first()
    if not tag:
        raise HTTPException(404, "Tag not found")
    
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted"}