# file: routers/products.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import JSONResponse
import models
from dependencies import db_dependency, user_dependency
import schemas 
from typing import List

router = APIRouter()

@router.get("/list", status_code=status.HTTP_200_OK,response_model=List[schemas.ProductResponse])
async def get_all_products(db: db_dependency):
    return db.query(models.Product).all()

@router.get("/get/{product_id}", status_code=status.HTTP_200_OK,response_model=schemas.ProductResponse)
async def product_information(db: db_dependency, product_id: int = Path(gt=0)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
@router.post(
    "/edits",
    response_model=schemas.ProductResponse,
    description="""
    This endpoint performs an explicit action on a product based on the `_action` field.

    - **`_action: "create"`**: Creates a new product. Requires `name`, `price`, etc.
    - **`_action: "update"`**: Updates an existing product. Requires `id` and fields to update.
    - **`_action: "archive"`**: Soft deletes a product. Requires `id`.
    """
)
async def product_edits_by_action(user: user_dependency, db: db_dependency, request: schemas.ProductUpsertRequest):
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized for this action.")
    
    action = request.action

    if action == schemas.ProductAction.CREATE:
        if request.name is None or request.price is None or request.quantity_in_stock is None:
            raise HTTPException(status_code=400, detail="Name, price, and quantity are required to create a product.")
        
        if db.query(models.Product).filter(models.Product.name == request.name).first():
            raise HTTPException(status_code=400, detail="Product with this name already exists")
        create_data = request.model_dump(exclude_unset=True, exclude={"id", "action"})
        new_product = models.Product(**create_data)
        new_product.is_active = new_product.quantity_in_stock > 0 
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    elif action == schemas.ProductAction.UPDATE:
        if request.id is None:
            raise HTTPException(status_code=400, detail="An 'id' is required for the 'update' action.")
        fetch_product = db.query(models.Product).filter(models.Product.id == request.id).first()
        if not fetch_product:
            raise HTTPException(status_code=404, detail="Product not found")
        update_data = request.model_dump(exclude_unset=True, exclude={"id", "action"})
        for key, value in update_data.items():
            setattr(fetch_product, key, value) 
        if 'quantity_in_stock' in update_data:
            fetch_product.is_active = fetch_product.quantity_in_stock > 0
            
        db.add(fetch_product)
        db.commit()
        db.refresh(fetch_product)
        return fetch_product
    
    elif action == schemas.ProductAction.DELETE:
        if request.id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="An 'id' must be provided to delete a product.")
        product_to_delete = db.query(models.Product).filter(models.Product.id == request.id).first()
        # order_items_with_product = db.query(models.OrderItem).filter(models.OrderItem.product_id == request.id).first()
        # # if order_items_with_product:
        # #      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Cannot delete product because it is an part of existing orders.")
        if not product_to_delete:
            raise HTTPException(status_code=404, detail="Product not found for deletion.")

        db.delete(product_to_delete)
        db.commit()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Product with id {request.id} was deleted successfully."})

# @router.post("/Product_edits")
# async def upsert_product(user: user_dependency,db: db_dependency,request: schemas.ProductUpsertRequest ):
#     if not user or user.get('role') != 'admin':
#         raise HTTPException(status_code=403, detail="Not authorized to perform this action.")
    
#     if request.action == 'delete':
#         if request.id is None:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="An 'id' must be provided to delete a product.")
#         product_to_delete = db.query(models.Product).filter(models.Product.id == request.id).first()
#         order_items_with_product = db.query(models.OrderItem).filter(models.OrderItem.product_id == request.id).first()
#         # if order_items_with_product:
#         #      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Cannot delete product because it is an part of existing orders.")
#         if not product_to_delete:
#             raise HTTPException(status_code=404, detail="Product not found for deletion.")

#         db.delete(product_to_delete)
#         db.commit()
#         return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Product with id {request.id} was deleted successfully."})


#     elif request.id is not None:
#         fetch_product = db.query(models.Product).filter(models.Product.id == request.id).first()
#         if not fetch_product:
#             raise HTTPException(status_code=404, detail="Product not found")
#         update_data = request.model_dump(exclude_unset=True,exclude={"id", "action"})
#         for key, value in update_data.items():
#             setattr(fetch_product, key, value)
#         if 'quantity_in_stock' in update_data and fetch_product.quantity_in_stock == 0:
#             fetch_product.is_active = False
#         db.add(fetch_product)
#         db.commit()
#         db.refresh(fetch_product)
#         return fetch_product
    
#     else:
#         if db.query(models.Product).filter(models.Product.name == request.name).first():
#             raise HTTPException(status_code=400, detail="Product already exists")
#         new_product = models.Product(**request.model_dump(exclude={"id", "action"}))
#         if new_product.quantity_in_stock == 0:
#             new_product.is_active = False
#         db.add(new_product)
#         db.commit()
#         db.refresh(new_product)
#         return new_product
# @router.post("/Newproduct", status_code=status.HTTP_201_CREATED,response_model=schemas.ProductResponse)
# async def create_product(user: user_dependency, db: db_dependency, request: schemas.ProductBase):
#     if not user or user.get('role') != 'admin':
#         raise HTTPException(status_code=403, detail="Not authorized to perform this action.")
#     if db.query(models.Product).filter(models.Product.name == request.name).first():
#         raise HTTPException(status_code=400, detail="Product already exists")
#     product = models.Product(**request.model_dump())
#     db.add(product)
#     db.refresh()
#     db.commit()
#     return product

# @router.patch("/update/{product_id}", status_code=status.HTTP_200_OK, response_model=schemas.ProductResponse)
# async def update_product(user: user_dependency, db: db_dependency, request: schemas.ProductUpdateRequest, product_id: int = Path(gt=0)):
#     if not user or user.get('role') != 'admin':
#         raise HTTPException(status_code=403, detail="Not authorized to perform this action.")

#     product_to_update = db.query(models.Product).filter(models.Product.id == product_id).first()
#     if product_to_update is None:
#         raise HTTPException(status_code=404, detail="Product not found")

#     # CHANGED: New logic to apply partial updates for any field sent by the client.
#     update_data = request.model_dump(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(product_to_update, key, value)

#     db.add(product_to_update)
#     db.commit()
#     db.refresh(product_to_update)
#     return product_to_update


# @router.delete("/delete/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_product(user: user_dependency, db: db_dependency, product_id: int = Path(gt=0)):
#     if not user or user.get('role') != 'admin':
#         raise HTTPException(status_code=403, detail="Not authorized to perform this action.")
#     delete_product = db.query(models.Product).filter(models.Product.id == product_id).first()
#     if delete_product is None:
#         raise HTTPException(status_code=404, detail="Product not found")
#     db.delete(delete_product)
#     db.commit()
#     return 

# @router.put("/stock_update/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def update_stock(user: user_dependency, db: db_dependency, request: schemas.StockUpdateRequest, product_id: int = Path(gt=0)):
#     if not user or user.get('role') != 'admin':
#         raise HTTPException(status_code=403, detail="Not authorized to perform this action.")
#     update_product = db.query(models.Product).filter(models.Product.id == product_id).first()
#     update_product.quantity_in_stock = request.quantity_in_stock
#     db.commit()
#     return update_product

# @router.put("/category/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def update_category(user: user_dependency, db: db_dependency, request: str, product_id: int = Path(gt=0)):
#     if not user or user.get('role') != 'admin':
#         raise HTTPException(status_code=403, detail="Not authorized to perform this action.")
#     update_product = db.query(models.Product).filter(models.Product.id == product_id).first()
#     update_product.category = request
#     db.commit()

@router.post(
    "/edits",
    response_model=schemas.ProductResponse,
    summary="Create, Update, or Archive a Product via Action",
    description="""
    This endpoint performs an explicit action on a product based on the `_action` field.

    - **`_action: "create"`**: Creates a new product. Requires `name`, `price`, etc.
    - **`_action: "update"`**: Updates an existing product. Requires `id` and fields to update.
    - **`_action: "archive"`**: Soft deletes a product. Requires `id`.
    """
)
async def product_edits_by_action(user: user_dependency, db: db_dependency, request: schemas.ProductUpsertRequest):
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized for this action.")
    
    action = request.action

    if action == schemas.ProductAction.CREATE:
        if request.name is None or request.price is None or request.quantity_in_stock is None:
            raise HTTPException(status_code=400, detail="Name, price, and quantity are required to create a product.")
        
        if db.query(models.Product).filter(models.Product.name == request.name).first():
            raise HTTPException(status_code=400, detail="Product with this name already exists")
        create_data = request.model_dump(exclude_unset=True, exclude={"id", "action"})
        new_product = models.Product(**create_data)
        new_product.is_active = new_product.quantity_in_stock > 0 
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    elif action == schemas.ProductAction.UPDATE:
        if request.id is None:
            raise HTTPException(status_code=400, detail="An 'id' is required for the 'update' action.")
        fetch_product = db.query(models.Product).filter(models.Product.id == request.id).first()
        if not fetch_product:
            raise HTTPException(status_code=404, detail="Product not found")
        update_data = request.model_dump(exclude_unset=True, exclude={"id", "action"})
        for key, value in update_data.items():
            setattr(fetch_product, key, value) 
        if 'quantity_in_stock' in update_data:
            fetch_product.is_active = fetch_product.quantity_in_stock > 0
            
        db.add(fetch_product)
        db.commit()
        db.refresh(fetch_product)
        return fetch_product
    
    elif action == schemas.ProductAction.DELETE:
        if request.id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="An 'id' must be provided to delete a product.")
        product_to_delete = db.query(models.Product).filter(models.Product.id == request.id).first()
        # order_items_with_product = db.query(models.OrderItem).filter(models.OrderItem.product_id == request.id).first()
        # # if order_items_with_product:
        # #      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Cannot delete product because it is an part of existing orders.")
        if not product_to_delete:
            raise HTTPException(status_code=404, detail="Product not found for deletion.")

        db.delete(product_to_delete)
        db.commit()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Product with id {request.id} was deleted successfully."})
