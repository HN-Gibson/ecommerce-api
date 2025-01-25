from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import DateTime, Float, ForeignKey, Table, Column, String, Integer, select
from marshmallow import ValidationError
from typing import List, Optional
from __future__ import annotations
import os
import datetime
from password import password

#=========== Initialize Flask app ==========

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{password}@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#========== Create Classes for SQL Database Tables ==========

#Declarative Class Base Model
class Base(DeclarativeBase):
    pass

#Initialize SQL ALchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

#User Model
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    street_address: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(5), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)

    orders: Mapped[List["Order"]] = relationship(back_populates="user")

#Order Model
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[DateTime] = mapped_column(DateTime, default = datetime.now)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="orders")

#Product Model
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float(10), nullable=False)

#Asociation Table for connecting Products and Orders
order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True, unique=True)
)

#========== Create Schemas for Validation, Serialization, and Deserialization ==========

#User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

#Order Schema
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order

#Product Schema
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

#Initialize Schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

#========== Create API Endpoints ==========

@app.route('/')
def home():
    return 'Welcome to my Flask E Commerce Application'

# User Endpoints
# GET /users: Retrieve all users

@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

# GET /users/<id>: Retrieve a user by ID
# POST /users: Create a new user
# PUT /users/<id>: Update a user by ID
# DELETE /users/<id>: Delete a user by ID

# Product Endpoints
# GET /products: Retrieve all products
# GET /products/<id>: Retrieve a product by ID
# POST /products: Create a new product
# PUT /products/<id>: Update a product by ID
# DELETE /products/<id>: Delete a product by ID

# Order Endpoints
# POST /orders: Create a new order (requires user ID and order date)
# GET /orders/<order_id>/add_product/<product_id>: Add a product to an order (prevent duplicates)
# DELETE /orders/<order_id>/remove_product: Remove a product from an order
# GET /orders/user/<user_id>: Get all orders for a user
# GET /orders/<order_id>/products: Get all products for an order