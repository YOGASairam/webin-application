# file: routers/orders.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import models
from sqlalchemy.sql import func
from dependencies import db_dependency, user_dependency
import schemas  # <-- Import schemas

router = APIRouter()

@router.post("/action")
async def manage_orders(user: user_dependency, db: db_dependency, request: schemas.OrderActionRequest):
    """
    Perform multiple actions on orders based on the `_action` field.
    - `list`: Get all orders for the current user.
    - `create`: Create a new order. Requires 'items'.
    - `cancel`: Cancel an existing order. Requires 'order_id'.
    """
    action = request.action
    
    if action == schemas.OrderAction.LIST:
        return db.query(models.Order).options(
            joinedload(models.Order.items).joinedload(models.OrderItem.product)
        ).filter(models.Order.owner_id == user.get('id')).all()

    elif action == schemas.OrderAction.CREATE:
        if not request.items:
            raise HTTPException(status_code=400, detail="The 'items' field is required to create an order.")

        total_price = 0.0
        discount_value = 0.0
        discount_obj = None

        if request.discount_code:
            discount_obj = db.query(models.DiscountCode).filter(
                models.DiscountCode.code == request.discount_code,
                models.DiscountCode.is_active == True
            ).first()

            if not discount_obj:
                raise HTTPException(status_code=400, detail="Invalid or inactive discount code.")
            if discount_obj.expiry_date and discount_obj.expiry_date < datetime.now():
                raise HTTPException(status_code=400, detail="The discount code has expired.")

        with db.begin_nested():
            new_order = models.Order(
                owner_id=user.get('id'),
                discount_code_id=discount_obj.id if discount_obj else None
            )
            db.add(new_order)
            db.flush()  
            
            for item_request in request.items:
                product = db.query(models.Product).filter(models.Product.id == item_request.product_id).first()
                if not product or product.quantity_in_stock < item_request.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Product ID {item_request.product_id} is unavailable or out of stock."
                    )

                line_price = product.price * item_request.quantity
                total_price += line_price

                order_item = models.OrderItem(
                    order_id=new_order.id,
                    product_id=item_request.product_id,
                    quantity=item_request.quantity
                )
                db.add(order_item)

                product.quantity_in_stock -= item_request.quantity
                db.add(product)

            if discount_obj:
                discount_value = (discount_obj.discount_percentage / 100) * total_price
                total_price -= discount_value

            new_order.total_price = round(total_price, 2)
            new_order.discount_applied = round(discount_value, 2)

        db.commit()


        final_order = db.query(models.Order).options(
            joinedload(models.Order.items).joinedload(models.OrderItem.product)
        ).filter(models.Order.id == new_order.id).first()

        return final_order

    elif action == schemas.OrderAction.CANCEL:
        if not request.order_id:
            raise HTTPException(status_code=400, detail="An 'order_id' is required to cancel an order.")

        order_to_cancel = db.query(models.Order).filter(
            models.Order.id == request.order_id,
            models.Order.owner_id == user.get('id')
        ).first()

        if not order_to_cancel:
            raise HTTPException(status_code=404, detail="Order not found or you are not the owner.")
        if order_to_cancel.status not in ["pending", "processing"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel an order with status '{order_to_cancel.status}'.")


        for item in order_to_cancel.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.quantity_in_stock += item.quantity
                db.add(product)

        order_to_cancel.status = "cancelled"
        db.add(order_to_cancel)
        db.commit()
        db.refresh(order_to_cancel)
        return order_to_cancel
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action specified.")


@router.get("/list_of_orders", status_code=status.HTTP_200_OK)
async def list_of_orders(user: user_dependency, db: db_dependency):
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized.")
    return db.query(models.Order).all()

@router.get("/price/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_price(user: user_dependency, db: db_dependency, order_id: int):
    if not user:
        raise HTTPException(status_code=403, detail="Not authorized.")

    order = db.query(models.Order).filter(models.Order.id == order_id, models.Order.owner_id == user.get('id')).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    return {"price": order.total_price}