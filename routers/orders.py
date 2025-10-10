# file: routers/orders.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import models
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
            joinedload(models.Order.items)
            .joinedload(models.OrderItem.product)
        ).filter(models.Order.owner_id == user.get('id')).all()
    elif action == schemas.OrderAction.CREATE:
        if not request.items:
            raise HTTPException(status_code=400, detail="The 'items' field is required to create an order.")
        
        with db.begin_nested():
            new_order = models.Order(owner_id=user.get('id'))
            db.add(new_order)
            db.flush()

            for item_request in request.items:
                product = db.query(models.Product).filter(models.Product.id == item_request.product_id).first()
                if not product or product.quantity_in_stock < item_request.quantity:
                    raise HTTPException(status_code=400, detail=f"Product ID {item_request.product_id} is unavailable or out of stock.")
                
                order_item = models.OrderItem(order_id=new_order.id, product_id=item_request.product_id, quantity=item_request.quantity)
                db.add(order_item)
                product.quantity_in_stock -= item_request.quantity
                db.add(product)
        
        db.commit()
        final_order = db.query(models.Order).options(joinedload(models.Order.items).joinedload(models.OrderItem.product)).filter(models.Order.id == new_order.id).first()
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

        order_to_cancel.status = 'cancelled'
        db.add(order_to_cancel)
        db.commit()
        db.refresh(order_to_cancel)
        return order_to_cancel

@router.get("/list_of_orders", status_code=status.HTTP_200_OK)
async def list_of_orders(user: user_dependency, db: db_dependency):
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized.")
    return db.query(models.Order).all()