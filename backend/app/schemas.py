from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- Auth ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str # "buyer" or "supplier"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        orm_mode = True

# --- Onboarding & Profiles ---
class BuyerOnboarding(BaseModel):
    business_type: Optional[str] = None
    industry: Optional[str] = None
    typical_order_qty: Optional[str] = None
    budget_range: Optional[str] = None
    preferred_climate: Optional[str] = None
    has_sensitive_skin: Optional[bool] = False
    skin_preferences: Optional[List[str]] = []

class SupplierOnboarding(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_info: Optional[str] = None
    address: Optional[str] = None
    operating_hours: Optional[str] = None
    categories: Optional[List[str]] = []

class BuyerProfileOut(BaseModel):
    business_type: Optional[str]
    industry: Optional[str]
    typical_order_qty: Optional[str]
    budget_range: Optional[str]
    preferred_climate: Optional[str]
    has_sensitive_skin: bool
    skin_preferences: Optional[List[str]] = []

    class Config:
        orm_mode = True

class SupplierProfileOut(BaseModel):
    business_name: Optional[str]
    business_type: Optional[str]
    contact_info: Optional[str]
    address: Optional[str]
    operating_hours: Optional[str]
    categories: Optional[List[str]] = []

    class Config:
        orm_mode = True

# --- Categories & Currencies ---
class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class CurrencyOut(BaseModel):
    id: int
    label: str
    symbol: str
    rate_to_usd: float

    class Config:
        orm_mode = True

# --- Product ---
class ProductBase(BaseModel):
    id: Optional[str] = None
    brand: Optional[str] = None
    name: str
    in_stock: bool
    gallery: Optional[List[str]] = []
    description: Optional[str] = None
    price_amount: float
    currency_symbol: str
    category_id: Optional[int] = None
    gsm: Optional[int] = None
    breathability_rating: Optional[int] = None
    is_hypoallergenic: Optional[bool] = False
    texture_smoothness: Optional[int] = None
    oeko_tex_certified: Optional[bool] = False
    recommended_climate: Optional[List[str]] = []

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    supplier_id: int

    class Config:
        orm_mode = True

# --- Orders ---
class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int
    price_amount: float

class OrderCreate(BaseModel):
    shipping_name: str
    shipping_address: str
    shipping_city: str
    shipping_country: str
    total_price: float
    currency_symbol: str
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    id: int
    product_id: str
    quantity: int
    price_amount: float

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id: int
    buyer_id: int
    shipping_name: str
    shipping_address: str
    shipping_city: str
    shipping_country: str
    status: str
    total_price: float
    currency_symbol: str
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        orm_mode = True

class OrderStatusUpdate(BaseModel):
    status: str

# --- Supplier Dashboard Widgets ---
class SupplierDashboardOut(BaseModel):
    total_products: int
    active_products: int
    pending_orders: int
    recent_orders: List[OrderOut]
    inventory_alerts: List[ProductOut]

# --- AI Chat Assistant ---
class AIChatMessage(BaseModel):
    role: str
    content: str

class AIChatRequest(BaseModel):
    message: str
    chat_history: List[AIChatMessage] = []

class AIChatResponse(BaseModel):
    response: str
    recommended_products: List[str]
