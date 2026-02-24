from sqlalchemy.orm import Session
from app.models.model_registry import ModelRegistry
from app.schemas.model_registry import ModelRegistryCreate, ModelRegistryUpdate
from typing import List, Optional, Tuple


def create_model(db: Session, model: ModelRegistryCreate, user_id: int) -> ModelRegistry:
    db_model = ModelRegistry(
        **model.model_dump(),
        created_by=user_id
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_models(db: Session, skip: int = 0, limit: int = 100) -> List[ModelRegistry]:
    return db.query(ModelRegistry).offset(skip).limit(limit).all()


def get_models_paginated(db: Session, skip: int = 0, limit: int = 10) -> Tuple[int, List[ModelRegistry]]:
    """
    Get paginated models with total count.
    
    Returns:
    - total: Total number of models
    - items: List of models for current page
    """
    query = db.query(ModelRegistry)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def get_model_by_id(db: Session, model_id: int) -> Optional[ModelRegistry]:
    return db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()


def update_model(db: Session, model_id: int, model_update: ModelRegistryUpdate) -> Optional[ModelRegistry]:
    db_model = get_model_by_id(db, model_id)
    if not db_model:
        return None
    
    update_data = model_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model(db: Session, model_id: int) -> bool:
    db_model = get_model_by_id(db, model_id)
    if not db_model:
        return False
    
    db.delete(db_model)
    db.commit()
    return True
