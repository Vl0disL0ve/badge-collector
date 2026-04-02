from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
from ..core import database, security
from ..models import User, Category, Set
from ..schemas import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()


@router.post("/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category = Category(
        user_id=current_user.id,
        name=data.name,
        description=data.description
    )
    db.add(category)
    db.flush()
    
    if data.set_ids:
        sets = db.query(Set).filter(
            Set.id.in_(data.set_ids),
            Set.user_id == current_user.id
        ).all()
        category.sets = sets
    
    db.commit()
    db.refresh(category)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        user_id=category.user_id,
        sets_count=len(category.sets),
        sets=[{"id": s.id, "name": s.name} for s in category.sets],
        created_at=category.created_at,
        updated_at=category.updated_at
    )


@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    categories = db.query(Category).filter(
        Category.user_id == current_user.id
    ).options(joinedload(Category.sets)).all()
    
    result = []
    for cat in categories:
        result.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            user_id=cat.user_id,
            sets_count=len(cat.sets),
            sets=[{"id": s.id, "name": s.name} for s in cat.sets],
            created_at=cat.created_at,
            updated_at=cat.updated_at
        ))
    return result


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).options(joinedload(Category.sets)).first()
    
    if not category:
        raise HTTPException(404, "Category not found")
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        user_id=category.user_id,
        sets_count=len(category.sets),
        sets=[{"id": s.id, "name": s.name} for s in category.sets],
        created_at=category.created_at,
        updated_at=category.updated_at
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(404, "Category not found")
    
    if data.name is not None:
        category.name = data.name
    if data.description is not None:
        category.description = data.description
    
    if data.set_ids is not None:
        sets = db.query(Set).filter(
            Set.id.in_(data.set_ids),
            Set.user_id == current_user.id
        ).all()
        category.sets = sets
    
    category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(category)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        user_id=category.user_id,
        sets_count=len(category.sets),
        sets=[{"id": s.id, "name": s.name} for s in category.sets],
        created_at=category.created_at,
        updated_at=category.updated_at
    )


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(404, "Category not found")
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}