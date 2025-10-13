# file: routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from textwrap import dedent

from typing import List
import models
from dependencies import db_dependency
from schemas import UserResponse
import schemas  

router = APIRouter()

@router.get("/list_of_users", status_code=status.HTTP_200_OK, response_model=List[schemas.UserResponse])
async def list_of_users(db: db_dependency):
    return db.query(models.User).all()

@router.post("/users/action",
             description="""
    This endpoint allows an admin to perform a specific action on a user.
    The action to be performed is specified in the request body using the `_action` field.

    ### Available Actions:

    * **`_action: "delete"`
    * **`_action: "deactivate"`
    * **`_action: "reactivate"`
    * **`_action: "promote"`
    * **`_action: "demote"`

    ### Request Body:
    
    A `user_id` must be provided in the request body for all actions.
    """)
async def user_action(db: db_dependency, request: schemas.AdminUserActionRequest):
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    action = request.action
    
    if action == schemas.AdminAction.DELETE:
        db.delete(user)
        db.commit()
        return JSONResponse(content={"message": f"User {request.user_id} was successfully deleted."})
    
    # All other actions are modifications
    if action == schemas.AdminAction.DEACTIVATE:
        user.is_active = False
    elif action == schemas.AdminAction.REACTIVATE:
        user.is_active = True
    elif action == schemas.AdminAction.PROMOTE:
        user.role = "admin"
    elif action == schemas.AdminAction.DEMOTE:
        user.role = "customer"
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)

