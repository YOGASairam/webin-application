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
    # Find the user first, since all actions need it
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if request.action == schemas.AdminAction.DELETE:
        db.delete(user)
        db.commit()
        return JSONResponse(content={"message": f"User {request.user_id} was successfully deleted."})
    elif request.action == schemas.AdminAction.DEACTIVATE:
        user.is_active = False
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    elif request.action == schemas.AdminAction.REACTIVATE:
        user.is_active = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    elif request.action == schemas.AdminAction.PROMOTE:
        user.role = "admin"
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    elif request.action == schemas.AdminAction.DEMOTE:
        user.role = "customer"
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    

@router.post(
    "/discounts/action",
    response_model=schemas.DiscountCodeResponse,
    summary="Create, Update, or Deactivate a Discount Code",
    description=dedent("""
        Performs an action on a discount code based on the `_action` field.

        - **`_action: "create"`**: Creates a new code.
        - **`_action: "update"`**: Updates an existing code.
        - **`_action: "deactivate"`**: Soft deletes a code by setting `is_active=false`.
        - **`_action: "delete"`**: Permanently deletes a code. **Warning: This is irreversible.**
    """)
)
async def manage_discount_code(db: db_dependency, request: schemas.DiscountActionRequest):
    action = request.action

    if action == schemas.DiscountCodeAction.CREATE:
        if not request.code or not request.discount_percentage:
            raise HTTPException(status_code=400, detail="`code` and `discount_percentage` are required for creation.")
        
        existing_code = db.query(models.DiscountCode).filter(models.DiscountCode.code == request.code).first()
        if existing_code:
            raise HTTPException(status_code=409, detail="A discount code with this code already exists.")
            
        new_code = models.DiscountCode(
            code=request.code,
            discount_percentage=request.discount_percentage,
            expiry_date=request.expiry_date
        )
        db.add(new_code)
        db.commit()
        db.refresh(new_code)
        return new_code
    if not request.id:
        raise HTTPException(status_code=400, detail=f"An `id` is required for the '{action}' action.")
        
    code_to_modify = db.query(models.DiscountCode).filter(models.DiscountCode.id == request.id).first()
    if not code_to_modify:
        raise HTTPException(status_code=404, detail="Discount code not found.")
    
    if action == schemas.DiscountCodeAction.DELETE:
        db.delete(code_to_modify)
        db.commit()
        return JSONResponse(content={"message": f"Discount code with id {request.id} has been permanently deleted."})

    elif action == schemas.DiscountCodeAction.UPDATE:
        update_data = request.model_dump(exclude_unset=True, exclude={'id', 'action', 'code'}) # Can't change the code itself
        for key, value in update_data.items():
            setattr(code_to_modify, key, value)
            
    elif action == schemas.DiscountCodeAction.DEACTIVATE:
        code_to_modify.is_active = False

    db.add(code_to_modify)
    db.commit()
    db.refresh(code_to_modify)
    return code_to_modify
    
