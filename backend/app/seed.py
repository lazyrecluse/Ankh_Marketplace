import json
from sqlalchemy.orm import Session
from . import models, auth

def seed_db_if_empty(db: Session):
    # Check if we already have categories seeded
    if db.query(models.Category).first() is not None:
        return # already seeded
        
    print("Seeding database with default categories, currencies, supplier, and products...")
    
    # 1. Seed Categories
    categories = ["all", "cotton", "silk", "linen"]
    for cat_name in categories:
        db.add(models.Category(name=cat_name))
        
    # 2. Seed Currencies
    currencies = [
        {"label": "USD", "symbol": "$"},
        {"label": "EUR", "symbol": "€"},
        {"label": "GBP", "symbol": "£"}
    ]
    for curr in currencies:
        db.add(models.Currency(label=curr["label"], symbol=curr["symbol"]))
        
    # 3. Seed Supplier User
    hashed_pwd = auth.get_password_hash("password")
    supplier = models.User(
        email="supplier@ankh.com",
        hashed_password=hashed_pwd,
        role="supplier"
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    # Supplier Profile
    supplier_profile = models.SupplierProfile(
        user_id=supplier.id,
        business_name="Ankh Eco Textiles Ltd",
        business_type="Manufacturer",
        contact_info="orders@ankhtextiles.com",
        address="12 Pharaohs Way, Cairo, Egypt",
        operating_hours="09:00 - 17:00 UTC",
        categories=json.dumps(["cotton", "silk", "linen"])
    )
    db.add(supplier_profile)
    
    # 4. Seed Products
    products = [
        {
            "id": "cotton-organic-1",
            "brand": "Ankh Eco Textiles",
            "name": "Organic Combed Cotton (Super Soft)",
            "in_stock": True,
            "gallery": json.dumps([
                "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=800",
                "https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?w=800"
            ]),
            "description": "High-grade 100% organic combed cotton fabric. Grown sustainably without toxic chemicals. Perfect for shirts, summer dresses, and baby clothing. Soft-to-touch with excellent breathability.",
            "price_amount": 12.50,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 150,
            "breathability_rating": 5,
            "is_hypoallergenic": True,
            "texture_smoothness": 4,
            "oeko_tex_certified": True,
            "recommended_climate": json.dumps(["Tropical", "Temperate"])
        },
        {
            "id": "silk-mulberry-1",
            "brand": "Ankh Eco Textiles",
            "name": "Premium Mulberry Silk 19 Momme",
            "in_stock": True,
            "gallery": json.dumps([
                "https://images.unsplash.com/photo-1606813907291-d86edd9b7226?w=800",
                "https://images.unsplash.com/photo-1576016770956-debb63d900ad?w=800"
            ]),
            "description": "100% Pure Mulberry Silk fabric of highest grade (6A). Ultra smooth texture reduces skin friction, making it ideal for hypoallergenic applications, bedding, sleepwear, and lining garments.",
            "price_amount": 45.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 80,
            "breathability_rating": 4,
            "is_hypoallergenic": True,
            "texture_smoothness": 5,
            "oeko_tex_certified": True,
            "recommended_climate": json.dumps(["Tropical", "Temperate", "Polar"])
        },
        {
            "id": "linen-belgian-1",
            "brand": "Ankh Eco Textiles",
            "name": "Heavyweight Belgian Linen Fabric",
            "in_stock": True,
            "gallery": json.dumps([
                "https://images.unsplash.com/photo-1618220179428-22790b461013?w=800",
                "https://images.unsplash.com/photo-1599387737286-29a3962533ca?w=800"
            ]),
            "description": "Thick yet extremely breathable Belgian linen fabric. Features a beautiful slubby texture that softens with every wash. Perfect for trousers, jackets, curtains, and high-durability apparel.",
            "price_amount": 22.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 240,
            "breathability_rating": 5,
            "is_hypoallergenic": True,
            "texture_smoothness": 3,
            "oeko_tex_certified": True,
            "recommended_climate": json.dumps(["Tropical", "Temperate"])
        },
        {
            "id": "wool-merino-1",
            "brand": "Ankh Eco Textiles",
            "name": "Superfine Merino Wool Knit",
            "in_stock": True,
            "gallery": json.dumps([
                "https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=800",
                "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=800"
            ]),
            "description": "Extra fine Merino Wool, perfect for cold winter insulation and high-performance base layers. It has active heat-retention properties and standard breathability.",
            "price_amount": 35.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 280,
            "breathability_rating": 3,
            "is_hypoallergenic": False,
            "texture_smoothness": 4,
            "oeko_tex_certified": True,
            "recommended_climate": json.dumps(["Polar", "Temperate"])
        }
    ]
    
    for p in products:
        db.add(models.Product(**p))
        
    db.commit()
    print("Database seeding completed.")
