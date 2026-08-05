import os
import uuid
import json
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import engine, get_db, Base
from . import models, schemas, auth
from .seed import seed_db_if_empty

# Create database tables
Base.metadata.create_all(bind=engine)

# Static file directory for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

tags_metadata = [
    {
        "name": "Auth",
        "description": "Operations with authentication, registration, login, and user profiles.",
    },
    {
        "name": "Onboarding",
        "description": "Onboarding forms and profile completions for Buyers and Suppliers.",
    },
    {
        "name": "Products",
        "description": "Catalog endpoints for categories, currencies, and products.",
    },
    {
        "name": "Orders",
        "description": "Checkout and order placement operations for Buyers.",
    },
    {
        "name": "Supplier",
        "description": "Supplier dashboard widgets, inventory CRUD, and order management.",
    },
]

app = FastAPI(
    title="Ankh B2B Textile Marketplace API",
    description="Full B2B Textile marketplace API documenting Auth, Onboarding, Products, Orders, and Dashboards.",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.post("/api/upload", tags=["Products"])
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
        
    file_url = f"/static/uploads/{filename}"
    return {"url": file_url, "image_url": file_url}

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        seed_db_if_empty(db)
    finally:
        db.close()

# --- AUTH ENDPOINTS ---

@app.post("/api/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pwd,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize basic profiles based on role
    if user.role == "buyer":
        profile = models.BuyerProfile(user_id=new_user.id)
        db.add(profile)
    else:
        profile = models.SupplierProfile(user_id=new_user.id)
        db.add(profile)
    db.commit()
    
    return new_user

@app.post("/api/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": db_user.role
    }

@app.get("/api/auth/me", tags=["Auth"])
def get_me(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    res = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }
    if current_user.role == "buyer":
        profile = db.query(models.BuyerProfile).filter(models.BuyerProfile.user_id == current_user.id).first()
        res["profile"] = {
            "business_type": profile.business_type if profile else None,
            "industry": profile.industry if profile else None,
            "typical_order_qty": profile.typical_order_qty if profile else None,
            "budget_range": profile.budget_range if profile else None,
            "preferred_climate": profile.preferred_climate if profile else None,
            "has_sensitive_skin": profile.has_sensitive_skin if profile else False,
            "skin_preferences": json.loads(profile.skin_preferences) if profile and profile.skin_preferences else []
        }
    else:
        profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == current_user.id).first()
        res["profile"] = {
            "business_name": profile.business_name if profile else None,
            "business_type": profile.business_type if profile else None,
            "contact_info": profile.contact_info if profile else None,
            "address": profile.address if profile else None,
            "operating_hours": profile.operating_hours if profile else None,
            "categories": json.loads(profile.categories) if profile and profile.categories else []
        }
    return res

# --- ONBOARDING ENDPOINTS ---

@app.post("/api/onboarding/buyer", tags=["Onboarding"])
def onboarding_buyer(profile_data: schemas.BuyerOnboarding, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can submit buyer onboarding details")
    
    profile = db.query(models.BuyerProfile).filter(models.BuyerProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.BuyerProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.business_type = profile_data.business_type
    profile.industry = profile_data.industry
    profile.typical_order_qty = profile_data.typical_order_qty
    profile.budget_range = profile_data.budget_range
    profile.preferred_climate = profile_data.preferred_climate
    profile.has_sensitive_skin = profile_data.has_sensitive_skin
    profile.skin_preferences = json.dumps(profile_data.skin_preferences)
    
    db.commit()
    return {"status": "success", "message": "Buyer onboarding completed successfully"}

@app.post("/api/onboarding/supplier", tags=["Onboarding"])
def onboarding_supplier(profile_data: schemas.SupplierOnboarding, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can submit supplier onboarding details")
    
    profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.SupplierProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.business_name = profile_data.business_name
    profile.business_type = profile_data.business_type
    profile.contact_info = profile_data.contact_info
    profile.address = profile_data.address
    profile.operating_hours = profile_data.operating_hours
    profile.categories = json.dumps(profile_data.categories)
    
    db.commit()
    return {"status": "success", "message": "Supplier onboarding completed successfully"}

# --- CATEGORY & CURRENCY ENDPOINTS ---

@app.get("/api/categories", tags=["Products"])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).all()
    return [{"name": c.name} for c in categories]

@app.get("/api/currencies", tags=["Products"])
def get_currencies(db: Session = Depends(get_db)):
    currencies = db.query(models.Currency).all()
    return [{"label": c.label, "symbol": c.symbol} for c in currencies]

def build_product_prices(base_amount: float) -> list:
    usd_amt = round(float(base_amount), 2)
    eur_amt = round(float(base_amount) * 0.92, 2)
    gbp_amt = round(float(base_amount) * 0.79, 2)
    return [
        {"currency": {"label": "USD", "symbol": "$"}, "amount": usd_amt},
        {"currency": {"label": "EUR", "symbol": "€"}, "amount": eur_amt},
        {"currency": {"label": "GBP", "symbol": "£"}, "amount": gbp_amt}
    ]

# --- PRODUCT ENDPOINTS ---

@app.get("/api/products", tags=["Products"])
def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    climate: Optional[str] = None,
    sensitive_skin: Optional[bool] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    
    if supplier_id is not None:
        query = query.filter(models.Product.supplier_id == supplier_id)
    
    if category and category.lower() != "all":
        # Check if product belongs to category. In current project, categories are Cotton, Silk, Linen, etc.
        # Products are filterable by category. We match the category name.
        # Since categories can be stored as uppercase in the DB or URL, match case insensitively or match exactly
        query = query.filter(models.Product.id.like(f"{category.lower()}%") | models.Product.name.like(f"%{category}%"))
    
    if search:
        query = query.filter(
            models.Product.name.like(f"%{search}%") | 
            models.Product.brand.like(f"%{search}%") | 
            models.Product.description.like(f"%{search}%")
        )
    
    products = query.all()
    
    # Python-side filtering for complex JSON lists (climates and skin sensitivity)
    filtered_products = []
    for p in products:
        # Match climate if specified
        if climate and climate.lower() != "all":
            climates = json.loads(p.recommended_climate) if p.recommended_climate else []
            # normalize check
            if not any(c.lower() == climate.lower() for c in climates) and "all" not in [c.lower() for c in climates]:
                continue
        
        # Match sensitive skin if specified
        if sensitive_skin:
            if not p.is_hypoallergenic:
                continue
                
        # Parse list representation for gallery
        gallery_list = json.loads(p.gallery) if p.gallery else []
        
        # Format prices to match the old schema expected by the frontend:
        # prices: [{ currency: { symbol: "$" }, amount: 120.00 }]
        # attributes: [] (or parsed from model attributes if added - we will mock or keep simple to match React views)
        formatted_product = {
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "inStock": p.in_stock,
            "gallery": gallery_list,
            "description": p.description,
            "prices": build_product_prices(p.price_amount),
            # To prevent front-end crash we must output empty attributes array if not defined
            "attributes": [
                {
                    "id": "Size",
                    "name": "Size",
                    "type": "text",
                    "items": [
                        {"id": "S", "value": "S", "displayValue": "Small"},
                        {"id": "M", "value": "M", "displayValue": "Medium"},
                        {"id": "L", "value": "L", "displayValue": "Large"}
                    ]
                }
            ],
            # AI recommendation metrics
            "gsm": p.gsm,
            "breathability_rating": p.breathability_rating,
            "is_hypoallergenic": p.is_hypoallergenic,
            "texture_smoothness": p.texture_smoothness,
            "oeko_tex_certified": p.oeko_tex_certified,
            "recommended_climate": json.loads(p.recommended_climate) if p.recommended_climate else []
        }
        filtered_products.append(formatted_product)
        
    return filtered_products

@app.get("/api/products/{product_id}", tags=["Products"])
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
        
    gallery_list = json.loads(p.gallery) if p.gallery else []
    return {
        "id": p.id,
        "brand": p.brand,
        "name": p.name,
        "inStock": p.in_stock,
        "gallery": gallery_list,
        "description": p.description,
        "prices": build_product_prices(p.price_amount),
        "attributes": [
            {
                "id": "Size",
                "name": "Size",
                "type": "text",
                "items": [
                    {"id": "S", "value": "S", "displayValue": "Small"},
                    {"id": "M", "value": "M", "displayValue": "Medium"},
                    {"id": "L", "value": "L", "displayValue": "Large"}
                ]
            }
        ],
        "gsm": p.gsm,
        "breathability_rating": p.breathability_rating,
        "is_hypoallergenic": p.is_hypoallergenic,
        "texture_smoothness": p.texture_smoothness,
        "oeko_tex_certified": p.oeko_tex_certified,
        "recommended_climate": json.loads(p.recommended_climate) if p.recommended_climate else []
    }

# --- BUYER ORDER & CHECKOUT ENDPOINTS ---

@app.post("/api/orders", tags=["Orders"])
def place_order(order_data: schemas.OrderCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can place orders")
        
    # Place order
    db_order = models.Order(
        buyer_id=current_user.id,
        shipping_name=order_data.shipping_name,
        shipping_address=order_data.shipping_address,
        shipping_city=order_data.shipping_city,
        shipping_country=order_data.shipping_country,
        status="Pending",
        total_price=order_data.total_price,
        currency_symbol=order_data.currency_symbol
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for item in order_data.items:
        # Check product exists
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not prod:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_amount=item.price_amount
        )
        db.add(db_item)
    
    db.commit()
    return {"status": "success", "message": "Order placed successfully", "order_id": db_order.id}

@app.get("/api/buyer/orders", tags=["Orders"])
def get_buyer_orders(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can access buyer orders")
        
    orders = db.query(models.Order).filter(models.Order.buyer_id == current_user.id).order_by(models.Order.created_at.desc()).all()
    
    res = []
    for o in orders:
        items = []
        for item in o.items:
            prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            items.append({
                "product_id": item.product_id,
                "product_name": prod.name if prod else "Unknown Fabric",
                "product_brand": prod.brand if prod else "Unknown Brand",
                "quantity": item.quantity,
                "price_amount": item.price_amount
            })
            
        res.append({
            "id": o.id,
            "shipping_name": o.shipping_name,
            "shipping_address": f"{o.shipping_address}, {o.shipping_city}, {o.shipping_country}",
            "status": o.status,
            "total_price": o.total_price,
            "currency_symbol": o.currency_symbol,
            "created_at": o.created_at,
            "items": items
        })
    return res

# --- SUPPLIER DASHBOARD & OPERATIONS ---

@app.get("/api/supplier/dashboard", response_model=schemas.SupplierDashboardOut, tags=["Supplier"])
def get_supplier_dashboard(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can access supplier dashboard")
        
    # Find all products supplied by this supplier
    products = db.query(models.Product).filter(models.Product.supplier_id == current_user.id).all()
    total_products = len(products)
    active_products = sum(1 for p in products if p.in_stock)
    
    # Find orders that contain at least one product from this supplier
    product_ids = [p.id for p in products]
    
    # Query orders containing these items
    supplier_order_items = db.query(models.OrderItem).filter(models.OrderItem.product_id.in_(product_ids)).all()
    order_ids = list(set([item.order_id for item in supplier_order_items]))
    
    orders = db.query(models.Order).filter(models.Order.id.in_(order_ids)).order_by(models.Order.created_at.desc()).all()
    
    pending_orders = sum(1 for o in orders if o.status == "Pending")
    
    # Inventory Alert: low/out-of-stock items (we can check if in_stock is False)
    # Parse gallery and recommended_climate JSON lists to avoid string splitting validation errors
    inventory_alerts = []
    for p in products:
        if not p.in_stock:
            inventory_alerts.append({
                "id": p.id,
                "brand": p.brand,
                "name": p.name,
                "in_stock": p.in_stock,
                "gallery": json.loads(p.gallery) if p.gallery else [],
                "description": p.description,
                "price_amount": p.price_amount,
                "currency_symbol": p.currency_symbol,
                "supplier_id": p.supplier_id,
                "gsm": p.gsm,
                "breathability_rating": p.breathability_rating,
                "is_hypoallergenic": p.is_hypoallergenic,
                "texture_smoothness": p.texture_smoothness,
                "oeko_tex_certified": p.oeko_tex_certified,
                "recommended_climate": json.loads(p.recommended_climate) if p.recommended_climate else []
            })
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "pending_orders": pending_orders,
        "recent_orders": orders[:5], # top 5
        "inventory_alerts": inventory_alerts
    }

@app.get("/api/supplier/orders", tags=["Supplier"])
def get_supplier_orders(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can access supplier orders")
        
    products = db.query(models.Product).filter(models.Product.supplier_id == current_user.id).all()
    product_ids = [p.id for p in products]
    
    supplier_order_items = db.query(models.OrderItem).filter(models.OrderItem.product_id.in_(product_ids)).all()
    order_ids = list(set([item.order_id for item in supplier_order_items]))
    
    orders = db.query(models.Order).filter(models.Order.id.in_(order_ids)).order_by(models.Order.created_at.desc()).all()
    
    res = []
    for o in orders:
        items = []
        for item in o.items:
            if item.product_id in product_ids:
                prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
                items.append({
                    "product_id": item.product_id,
                    "product_name": prod.name if prod else "Unknown",
                    "quantity": item.quantity,
                    "price_amount": item.price_amount
                })
        res.append({
            "id": o.id,
            "shipping_name": o.shipping_name,
            "shipping_address": f"{o.shipping_address}, {o.shipping_city}, {o.shipping_country}",
            "status": o.status,
            "total_price": o.total_price,
            "currency_symbol": o.currency_symbol,
            "created_at": o.created_at,
            "items": items
        })
    return res

@app.put("/api/supplier/orders/{order_id}/status", tags=["Supplier"])
def update_supplier_order_status(order_id: int, status_update: schemas.OrderStatusUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can update order statuses")
        
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Verify this order belongs to products of this supplier
    products = db.query(models.Product).filter(models.Product.supplier_id == current_user.id).all()
    product_ids = [p.id for p in products]
    
    has_supplier_product = any(item.product_id in product_ids for item in order.items)
    if not has_supplier_product:
        raise HTTPException(status_code=403, detail="Not authorized to update status for this order")
        
    order.status = status_update.status
    db.commit()
    return {"status": "success", "message": f"Order status updated to {status_update.status}"}

@app.post("/api/supplier/products", tags=["Supplier"])
def add_supplier_product(product_data: schemas.ProductCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can add products")
        
    db_product = db.query(models.Product).filter(models.Product.id == product_data.id).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product ID already exists")
        
    new_prod = models.Product(
        id=product_data.id,
        brand=product_data.brand,
        name=product_data.name,
        in_stock=product_data.in_stock,
        gallery=json.dumps(product_data.gallery),
        description=product_data.description,
        price_amount=product_data.price_amount,
        currency_symbol=product_data.currency_symbol,
        supplier_id=current_user.id,
        gsm=product_data.gsm,
        breathability_rating=product_data.breathability_rating,
        is_hypoallergenic=product_data.is_hypoallergenic,
        texture_smoothness=product_data.texture_smoothness,
        oeko_tex_certified=product_data.oeko_tex_certified,
        recommended_climate=json.dumps(product_data.recommended_climate)
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return {"status": "success", "message": "Product created successfully"}

@app.put("/api/supplier/products/{product_id}", tags=["Supplier"])
def update_supplier_product(product_id: str, product_data: schemas.ProductCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can update products")
        
    prod = db.query(models.Product).filter(models.Product.id == product_id, models.Product.supplier_id == current_user.id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found or not owned by supplier")
        
    prod.brand = product_data.brand
    prod.name = product_data.name
    prod.in_stock = product_data.in_stock
    prod.gallery = json.dumps(product_data.gallery)
    prod.description = product_data.description
    prod.price_amount = product_data.price_amount
    prod.currency_symbol = product_data.currency_symbol
    prod.gsm = product_data.gsm
    prod.breathability_rating = product_data.breathability_rating
    prod.is_hypoallergenic = product_data.is_hypoallergenic
    prod.texture_smoothness = product_data.texture_smoothness
    prod.oeko_tex_certified = product_data.oeko_tex_certified
    prod.recommended_climate = json.dumps(product_data.recommended_climate)
    
    db.commit()
    return {"status": "success", "message": "Product updated successfully"}

@app.delete("/api/supplier/products/{product_id}", tags=["Supplier"])
def delete_supplier_product(product_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "supplier":
        raise HTTPException(status_code=403, detail="Only suppliers can delete products")
        
    prod = db.query(models.Product).filter(models.Product.id == product_id, models.Product.supplier_id == current_user.id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found or not owned by supplier")
        
    db.delete(prod)
    db.commit()
    return {"status": "success", "message": "Product deleted successfully"}
