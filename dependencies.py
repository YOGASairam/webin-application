# File: dependencies.py

from fastapi import Depends, HTTPException, status
from typing import Annotated
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal

# --- Copy these from auth.py ---
SECRET_KEY = '5300250d7b66e3f33c28ee7b6cbe94a8a7630dd9341116044bdfeaf6038da8e7'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=30

# --------------------------------

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user credentials')
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user credentials')

user_dependency = Annotated[dict, Depends(get_current_user)]

async def get_current_admin_user(user: user_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )
    return user

admin_user_dependency = Annotated[dict, Depends(get_current_admin_user)]
