# file: routers/auth.py

from fastapi import APIRouter, Depends, status, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from datetime import timedelta, datetime, timezone
from typing import Annotated
import models
from dependencies import db_dependency, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import schemas  # <-- Import schemas

router = APIRouter(
)

bcrypt_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return bcrypt_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: schemas.CreateUserRequest):
    existing_user_check = db.query(models.User).filter((models.User.username == create_user_request.username)|(models.User.email == create_user_request.email)).first()
    if existing_user_check:
        if existing_user_check.username == create_user_request.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists.")
        if existing_user_check.email == create_user_request.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user_model = models.User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=get_password_hash(create_user_request.password),
        is_active=True,
        # phone_number=create_user_request.phone_number
    )
    db.add(user_model)
    db.commit()
    return {"message": f"User '{create_user_request.username}' created successfully."}

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user.username, "id": user.id, "role": user.role}
    token = create_access_token(token_data, expires)

    return {'access_token': token, 'token_type': 'bearer'}