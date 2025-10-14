# file: models.py (Final Cleaned Version)

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, nullable=False)
    phone_number = Column(String, nullable=True) # Enabled
    age = Column(Integer, nullable=True)         # Enabled
    
    orders = relationship("Order", back_populates="owner")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float, nullable=False)
    quantity_in_stock = Column(Integer, default=0)
    is_active = Column(Boolean, nullable=False, server_default='true')
    # category = Column(String, nullable=True, index=True) # Enabled

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default='pending')
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # total_price = Column(Float, nullable=False, default=0.0)
    # discount_applied = Column(Float, nullable=True, default=0.0)
    # discount_code_id = Column(Integer, ForeignKey("discount_codes.id"), nullable=True)

    owner = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    
class DiscountCode(Base):
    __tablename__ = "discount_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_percentage = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default='true')
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())