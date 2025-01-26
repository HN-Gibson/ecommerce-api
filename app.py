from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import sqlalchemy
import sqlalchemy.exc
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import DateTime, Float, ForeignKey, Table, Column, String, Integer, select
from marshmallow import ValidationError
from typing import List, Optional
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

#Association Table for connecting Users and Orders
user_order = Table(
    "user_order",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("order_id", ForeignKey("orders.id"), primary_key=True)
)

#Asociation Table for connecting Products and Orders
order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)

#User Model
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    street_address: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(5), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    user_orders: Mapped[List["Order"]] = relationship("Order", secondary=user_order, back_populates="ordered_by")

#Order Model
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[DateTime] = mapped_column(DateTime, default = datetime.datetime.now())
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"))

    ordered_by: Mapped["User"] = relationship("User", secondary=user_order, back_populates="user_orders")
    included_products: Mapped[List["Product"]] = relationship("Product", secondary=order_product, back_populates="in_orders")

#Product Model
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    price: Mapped[float] = mapped_column(Float(10), nullable=False)

    in_orders: Mapped[List["Order"]] = relationship("Order", secondary=order_product, back_populates="included_products")



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



#========== API Endpoints ==========

@app.route('/')
def home():
    return 'Welcome to my E Commerce API'



#========== User Endpoints ===========

#===== Retrieve all users

@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

#===== Retrieve a user by ID

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200

#===== Create a new user

@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    try:
        new_user = User(name=user_data['name'], street_address=user_data['street_address'], city=user_data['city'], state=user_data['state'], zip_code=user_data['zip_code'], email=user_data['email'])
        db.session.add(new_user)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        return jsonify({"message": "User with e-mail already exists!"})

    return jsonify({"message": f"{new_user.name} successfully added!"}), 201

#===== Update a user by ID

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.street_address = user_data['street_address']
    user.city = user_data['city']
    user.state = user_data['state']
    user.zip_code = user_data['zip_code']
    user.email = user_data['email']

    db.session.commit()
    return user_schema.jsonify(user), 200

#===== Delete a user by ID

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succefully deleted user {id}"}), 200



#========== Product Endpoints ==========

#===== Retrieve all products

@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    users = db.session.execute(query).scalars().all()

    return products_schema.jsonify(users), 200

#===== Retrieve a product by ID

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    user = db.session.get(Product, id)
    return product_schema.jsonify(user), 200

#===== Create a new product

@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    try:
        new_product = Product(name=product_data['name'], price=product_data['price'])
        db.session.add(new_product)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        return jsonify({"message": "Product with name already exists!"})

    return jsonify({"message": f"{new_product.name} successfully added!"}), 201

#===== Update a product by ID

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200

#===== Delete a product by ID

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"succefully deleted product {id}"}), 200



#========== Order Endpoints ==========

#===== Create a new order (requires user ID and order date)

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()

    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user id'}), 400

    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    order = Order(user_id=user.id)
    db.session.add(order)

    user.user_orders.append(order)

    db.session.commit()

    return jsonify({"message": f"{user.name} successfully added an order!"}), 201

#===== Add a product to an order (prevent duplicates)

@app.route('/orders/<order_id>/add_product/<product_id>', methods=['GET'])
def add_product_to_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)

    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product in order.included_products:
        return jsonify({'error': 'Product already in order'}), 400
    
    order.included_products.append(product)

    db.session.commit()

    return jsonify({"message": f"{product.name} added to order # {order.id}"})

#===== Remove a product from an order

@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = db.session.get(Order, id)

    if not order:
        return jsonify({"message": "Invalid order id"}), 400

    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": f"succefully deleted order {id}"}), 200

#===== Get all orders for a user

@app.route('/orders/user/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    orders = user.user_orders
    orders_by_user = []
    for order in orders:
        orders_by_user.append(order.id)
    return jsonify({"message": f"Order(s) # {orders_by_user} are the orders associated with {user.name}"})


#===== Get all products for an order

@app.route('/orders/<order_id>/products', methods=['GET'])
def get_all_order_products(order_id):
    order = db.session.get(Order, order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404   

    products = order.included_products
    products_in_order = []

    for product in products:
        products_in_order.append(product.name)
    
    return jsonify({"message": f"Order # {order.id} contents: {products_in_order}"})


#========== App Initialization ========== (Comment or uncomment 'drop_all' or 'create_all' to clear database or establish tables in database respectively.)

if __name__ == "__main__":
    with app.app_context():
        # db.drop_all()
        db.create_all()

    app.run(debug=True)