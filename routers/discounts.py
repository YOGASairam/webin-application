# file: routers/discounts.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from textwrap import dedent
import models
from dependencies import db_dependency, admin_user_dependency
import schemas

router = APIRouter()

@router.post(
    "/discounts/action",
    summary="Perform any action on a Discount Code",
    description=dedent("""
        Performs a specific action on a discount code based on the `_action` field in the request body.

        ### Actions & Required Fields:

        * **`_action: "create"`**: Creates a new discount code.
            - **Requires:** `code`, `discount_percentage`
            - *Optional:* `expiry_date`

        * **`_action: "update"`**: Updates an existing discount code.
            - **Requires:** `id`
            - *Optional:* `discount_percentage`, `is_active`, `expiry_date`

        * **`_action: "deactivate"`**: Soft deletes a code by setting `is_active=false`.
            - **Requires:** `id`

        * **`_action: "delete"`**: Permanently deletes a discount code from the database.
            - **Requires:** `id`
            - **Warning:** This action is irreversible.
    """)
)
async def manage_discount_code(db: db_dependency, request: schemas.DiscountActionRequest):
    action = request.action

    # --- CREATE LOGIC ---
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

    # --- All other actions require an ID ---
    if not request.id:
        raise HTTPException(status_code=400, detail=f"An `id` is required for the '{action}' action.")
        
    code_to_modify = db.query(models.DiscountCode).filter(models.DiscountCode.id == request.id).first()
    if not code_to_modify:
        raise HTTPException(status_code=404, detail="Discount code not found.")

    # --- DELETE (HARD DELETE) LOGIC ---
    if action == schemas.DiscountCodeAction.DELETE:
        db.delete(code_to_modify)
        db.commit()
        return JSONResponse(content={"message": f"Discount code with id {request.id} has been permanently deleted."})

    # --- UPDATE LOGIC ---
    elif action == schemas.DiscountCodeAction.UPDATE:
        update_data = request.model_dump(exclude_unset=True, exclude={'id', 'action', 'code'})
        for key, value in update_data.items():
            setattr(code_to_modify, key, value)

    # --- DEACTIVATE (SOFT DELETE) LOGIC ---
    elif action == schemas.DiscountCodeAction.DEACTIVATE:
        code_to_modify.is_active = False

    db.add(code_to_modify)
    db.commit()
    db.refresh(code_to_modify)
    return code_to_modify

@router.get("/{code_id}", response_model=schemas.DiscountCodeResponse, summary="Get a Discount Code by ID")
async def get_discount_code(db: db_dependency, code_id: int = Path(gt=0)):
    """
    Get a discount code by its ID. (Admin only)
    """
    code = db.query(models.DiscountCode).filter(models.DiscountCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Discount code not found.")
    return code
