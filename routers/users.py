# file: routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
import models
from dependencies import db_dependency, user_dependency
import schemas  # <-- Import schemas

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    return db.query(models.User).filter(models.User.id == user.get('id')).first()

@router.put("/password_change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: schemas.UserPasswordRequest):
    user_model = db.query(models.User).filter(models.User.id == user.get('id')).first()
    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect Password")
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()
    
@router.patch("/modify_details", status_code=status.HTTP_200_OK)
async def modify_user_details(user: user_dependency, db: db_dependency, request: schemas.UserBase):
    user_model = db.query(models.User).filter(models.User.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_model, key, value)
    db.add(user_model)       
    db.commit()
    db.refresh(user_model)   
    return user_model
    
