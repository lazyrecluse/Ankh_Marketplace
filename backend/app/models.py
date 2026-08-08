import datetime
from sqlalchemy import JSON, Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False) # "buyer" or "supplier"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False)
    supplier_profile = relationship("SupplierProfile", back_populates="user", uselist=False)
    products = relationship("Product", back_populates="supplier")
    orders = relationship("Order", back_populates="buyer")

class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    business_type = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    typical_order_qty = Column(String, nullable=True)
    budget_range = Column(String, nullable=True)
    
    # Climate and Sensitivity preferences for AI
    preferred_climate = Column(String, nullable=True) # "Tropical", "Temperate", "Polar", "All"
    has_sensitive_skin = Column(Boolean, default=False)
    # e.g. ["Hypoallergenic Only", "Ultra Soft Only"]. SQLite stores JSON as
    # TEXT, so this is on-disk identical to the old hand-serialized column.
    skin_preferences = Column(JSON, nullable=True, default=list)

    user = relationship("User", back_populates="buyer_profile")

class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    business_name = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    contact_info = Column(String, nullable=True)
    address = Column(String, nullable=True)
    operating_hours = Column(String, nullable=True)
    categories = Column(JSON, nullable=True, default=list) # list of category names

    user = relationship("User", back_populates="supplier_profile")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, unique=True, index=True, nullable=False)
    symbol = Column(String, nullable=False)
    # Multiplier applied to a product's stored USD price_amount. USD is 1.0.
    # Replaces the 0.92/0.79 constants that used to be hardcoded in
    # build_product_prices().
    rate_to_usd = Column(Float, nullable=False, default=1.0)

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True) # E.g. unique product ID slug or string
    brand = Column(String, nullable=False)
    name = Column(String, nullable=False)
    in_stock = Column(Boolean, default=True)
    gallery = Column(JSON, nullable=False, default=list) # list of image URLs
    description = Column(Text, nullable=True)
    price_amount = Column(Float, nullable=False)
    currency_symbol = Column(String, nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Replaces the `id LIKE 'cotton%' OR name LIKE '%cotton%'` filter that
    # GET /api/products used to run, which existed only because products had
    # no category of their own.
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)

    # AI Recommendation Engine Fields
    gsm = Column(Integer, nullable=True) # Fabric weight
    breathability_rating = Column(Integer, nullable=True) # 1-5
    is_hypoallergenic = Column(Boolean, default=False)
    texture_smoothness = Column(Integer, nullable=True) # 1-5
    oeko_tex_certified = Column(Boolean, default=False)
    recommended_climate = Column(JSON, nullable=True, default=list) # e.g. ["Tropical"]

    supplier = relationship("User", back_populates="products")
    category = relationship("Category")
    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shipping_name = Column(String, nullable=False)
    shipping_address = Column(String, nullable=False)
    shipping_city = Column(String, nullable=False)
    shipping_country = Column(String, nullable=False)
    status = Column(String, default="Pending") # "Pending", "Accepted", "Preparing", "Ready for Dispatch", "Completed"
    total_price = Column(Float, nullable=False)
    currency_symbol = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    buyer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_amount = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
