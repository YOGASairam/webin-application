# file: schemas.py (Final Cleaned Version)

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# ===============================================
#                 SCHEMAS: TOKEN
# ===============================================

class Token(BaseModel):
    access_token: str
    token_type: str

# ===============================================
#                  SCHEMAS: USER
# ===============================================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3)
    email: str
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)

class CreateUserRequest(UserBase):
    password: str = Field(..., min_length=6, max_length=72)
    role: str = "customer"

class UserResponse(UserBase):
    id: int
    is_active: bool
    phone_number: Optional[str] = None
    age: Optional[int] = None
    role: str

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=2)
    last_name: Optional[str] = Field(None, min_length=2)
    phone_number: Optional[str] = None
    age: Optional[int] = Field(None, gt=0)

class UserPasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=72)
    new_password: str = Field(..., min_length=6, max_length=72)

# ===============================================
#                SCHEMAS: PRODUCT
# ===============================================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=3)
    description: str = Field(..., min_length=3, max_length=1000)
    price: float = Field(..., gt=0)
    quantity_in_stock: int = Field(..., ge=0)
    category: Optional[str] = None

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3)
    description: Optional[str] = Field(None, min_length=3, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    quantity_in_stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=3)
    is_active: Optional[bool] = None

class ProductAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    ARCHIVE = "archive"

class ProductUpsertRequest(BaseModel):
    action: ProductAction = Field(..., alias='_action')
    id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=3)
    description: Optional[str] = Field(None, min_length=3, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    quantity_in_stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# ===============================================
#                  SCHEMAS: ORDER
# ===============================================

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderRequest(BaseModel):
    items: List[OrderItemBase]

class ProductInOrderResponse(BaseModel):
    id: int
    name: str
    price: float
    
    class Config:
        from_attributes = True

class OrderItemResponse(OrderItemBase):
    id: int
    product: ProductInOrderResponse

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_date: datetime
    status: str
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., min_length=3)

class OrderAction(str, Enum):
    LIST = "list"
    CREATE = "create"
    CANCEL = "cancel"

class OrderActionRequest(BaseModel):
    action: OrderAction = Field(..., alias='_action')
    order_id: Optional[int] = None
    items: Optional[List[OrderItemBase]] = None

# ===============================================
#                  SCHEMAS: ADMIN
# ===============================================

class AdminAction(str, Enum):
    DELETE = "delete"
    DEACTIVATE = "deactivate"
    REACTIVATE = "reactivate"
    PROMOTE = "promote"
    DEMOTE = "demote"

class AdminUserActionRequest(BaseModel):
    action: AdminAction = Field(..., alias='_action')
    user_id: int

# ===============================================
#              SCHEMAS: DISCOUNT CODE
# ===============================================

class DiscountCodeBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=20)
    discount_percentage: int = Field(..., gt=0, lt=100)
    expiry_date: Optional[datetime] = None

class DiscountCodeCreate(DiscountCodeBase):
    pass

class DiscountCodeUpdate(BaseModel):
    discount_percentage: Optional[int] = Field(None, gt=0, lt=100)
    is_active: Optional[bool] = None
    expiry_date: Optional[datetime] = None

class DiscountCodeResponse(DiscountCodeBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DiscountCodeAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DEACTIVATE = "deactivate"
    DELETE = "delete"

class DiscountActionRequest(BaseModel):
    action: DiscountCodeAction = Field(..., alias="_action")
    id: Optional[int] = None
    code: Optional[str] = Field(None, min_length=3, max_length=20)
    discount_percentage: Optional[int] = Field(None, gt=0, lt=100)
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None