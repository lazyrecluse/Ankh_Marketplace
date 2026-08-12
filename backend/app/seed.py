from sqlalchemy.orm import Session
from . import models, security

# Product slug -> category name. Spelled out rather than derived from the slug
# prefix, because "wool-merino-1" belongs to "woolen" and prefix matching alone
# would leave it uncategorised.
PRODUCT_CATEGORIES = {
    "cotton-organic-1": "cotton",
    "silk-mulberry-1": "silk",
    "linen-belgian-1": "linen",
    "wool-merino-1": "woolen",
    "woolen-fabric-prod": "woolen",
    "mohair-fabric-prod": "mohair",
    "ankara-fabric-prod": "ankara",
    "kente-fabric-prod": "kente",
    "velvet-fabric-prod": "velvet",
    "cashmere-fabric-prod": "cashmere",
}

SUPPLIER_CATEGORIES = [
    "cotton", "silk", "linen", "woolen", "mohair",
    "ankara", "kente", "velvet", "cashmere",
]

def seed_db_if_empty(db: Session):
    print("Checking and seeding database with categories, currencies, supplier, and products...")
    
    # 1. Seed Categories
    categories = ["all", "cotton", "silk", "linen", "woolen", "mohair", "ankara", "kente", "velvet", "cashmere"]
    for cat_name in categories:
        if not db.query(models.Category).filter(models.Category.name == cat_name).first():
            db.add(models.Category(name=cat_name))
    db.commit()
        
    # 2. Seed Currencies
    # rate_to_usd multiplies a product's stored USD price. These are the same
    # constants build_product_prices() used to hardcode.
    currencies = [
        {"label": "USD", "symbol": "$", "rate_to_usd": 1.0},
        {"label": "EUR", "symbol": "€", "rate_to_usd": 0.92},
        {"label": "GBP", "symbol": "£", "rate_to_usd": 0.79}
    ]
    for curr in currencies:
        existing = db.query(models.Currency).filter(models.Currency.label == curr["label"]).first()
        if not existing:
            db.add(models.Currency(**curr))
        else:
            existing.rate_to_usd = curr["rate_to_usd"]
    db.commit()
        
    # 3. Seed Supplier User
    supplier = db.query(models.User).filter(models.User.email == "supplier@ankh.com").first()
    if not supplier:
        hashed_pwd = security.get_password_hash("password")
        supplier = models.User(
            email="supplier@ankh.com",
            hashed_password=hashed_pwd,
            role="supplier"
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
    
    # Supplier Profile
    supplier_profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == supplier.id).first()
    if not supplier_profile:
        supplier_profile = models.SupplierProfile(
            user_id=supplier.id,
            business_name="Ankh Eco Textiles Ltd",
            business_type="Manufacturer",
            contact_info="orders@ankhtextiles.com",
            address="12 Pharaohs Way, Cairo, Egypt",
            operating_hours="09:00 - 17:00 UTC",
            categories=SUPPLIER_CATEGORIES
        )
        db.add(supplier_profile)
        db.commit()
    else:
        # Update categories on existing supplier profile
        supplier_profile.categories = SUPPLIER_CATEGORIES
        db.commit()

    # 4. Seed Products
    products = [
        {
            "id": "cotton-organic-1",
            "brand": "Ankh Eco Textiles",
            "name": "Organic Combed Cotton (Super Soft)",
            "in_stock": True,
            "gallery": [
                "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=800",
                "https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?w=800"
            ],
            "description": "High-grade 100% organic combed cotton fabric. Grown sustainably without toxic chemicals. Perfect for shirts, summer dresses, and baby clothing. Soft-to-touch with excellent breathability.",
            "price_amount": 12.50,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 150,
            "breathability_rating": 5,
            "is_hypoallergenic": True,
            "texture_smoothness": 4,
            "oeko_tex_certified": True,
            "recommended_climate": ["Tropical", "Temperate"]
        },
        {
            "id": "silk-mulberry-1",
            "brand": "Ankh Eco Textiles",
            "name": "Premium Mulberry Silk 19 Momme",
            "in_stock": True,
            "gallery": [
                "https://images.unsplash.com/photo-1606813907291-d86edd9b7226?w=800",
                "https://images.unsplash.com/photo-1576016770956-debb63d900ad?w=800"
            ],
            "description": "100% Pure Mulberry Silk fabric of highest grade (6A). Ultra smooth texture reduces skin friction, making it ideal for hypoallergenic applications, bedding, sleepwear, and lining garments.",
            "price_amount": 45.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 80,
            "breathability_rating": 4,
            "is_hypoallergenic": True,
            "texture_smoothness": 5,
            "oeko_tex_certified": True,
            "recommended_climate": ["Tropical", "Temperate", "Polar"]
        },
        {
            "id": "linen-belgian-1",
            "brand": "Ankh Eco Textiles",
            "name": "Heavyweight Belgian Linen Fabric",
            "in_stock": True,
            "gallery": [
                "https://images.unsplash.com/photo-1618220179428-22790b461013?w=800",
                "https://images.unsplash.com/photo-1599387737286-29a3962533ca?w=800"
            ],
            "description": "Thick yet extremely breathable Belgian linen fabric. Features a beautiful slubby texture that softens with every wash. Perfect for trousers, jackets, curtains, and high-durability apparel.",
            "price_amount": 22.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 240,
            "breathability_rating": 5,
            "is_hypoallergenic": True,
            "texture_smoothness": 3,
            "oeko_tex_certified": True,
            "recommended_climate": ["Tropical", "Temperate"]
        },
        {
            "id": "wool-merino-1",
            "brand": "Ankh Eco Textiles",
            "name": "Superfine Merino Wool Knit",
            "in_stock": True,
            "gallery": [
                "https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=800",
                "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=800"
            ],
            "description": "Extra fine Merino Wool, perfect for cold winter insulation and high-performance base layers. It has active heat-retention properties and standard breathability.",
            "price_amount": 35.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 280,
            "breathability_rating": 3,
            "is_hypoallergenic": False,
            "texture_smoothness": 4,
            "oeko_tex_certified": True,
            "recommended_climate": ["Polar", "Temperate"]
        },
        {
            "id": "woolen-fabric-prod",
            "brand": "Ankh Eco Textiles",
            "name": "Premium Woolen Weave",
            "in_stock": True,
            "gallery": ["https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=800"],
            "description": "Pure woolen fabric with excellent warmth retention, perfect for coats and heavy winter clothing.",
            "price_amount": 28.50,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 320,
            "breathability_rating": 2,
            "is_hypoallergenic": False,
            "texture_smoothness": 2,
            "oeko_tex_certified": True,
            "recommended_climate": ["Polar", "Temperate"]
        },
        {
            "id": "mohair-fabric-prod",
            "brand": "Ankh Eco Textiles",
            "name": "Luxury Mohair Blend",
            "in_stock": True,
            "gallery": ["https://images.unsplash.com/photo-1565084888279-aca607ecce0c?w=800"],
            "description": "High-end mohair blend fabric, soft, silk-like, and highly durable.",
            "price_amount": 38.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 220,
            "breathability_rating": 3,
            "is_hypoallergenic": True,
            "texture_smoothness": 4,
            "oeko_tex_certified": True,
            "recommended_climate": ["Polar", "Temperate"]
        },
        {
            "id": "ankara-fabric-prod",
            "brand": "Ankh Eco Textiles",
            "name": "Vibrant Ankara Wax Print",
            "in_stock": True,
            "gallery": ["https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800"],
            "description": "Authentic Ankara African wax print fabric with beautiful vibrant patterns, 100% cotton.",
            "price_amount": 15.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 160,
            "breathability_rating": 4,
            "is_hypoallergenic": True,
            "texture_smoothness": 3,
            "oeko_tex_certified": True,
            "recommended_climate": ["Tropical", "Temperate"]
        },
        {
            "id": "kente-fabric-prod",
            "brand": "Ankh Eco Textiles",
            "name": "Traditional Woven Kente",
            "in_stock": True,
            "gallery": ["https://images.unsplash.com/photo-1596993100471-c3905dafa78e?w=800"],
            "description": "Stunning handwoven Kente fabric with intricate geometric designs and rich colors.",
            "price_amount": 32.50,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 200,
            "breathability_rating": 4,
            "is_hypoallergenic": True,
            "texture_smoothness": 3,
            "oeko_tex_certified": True,
            "recommended_climate": ["Tropical", "Temperate"]
        },
        {
            "id": "velvet-fabric-prod",
            "brand": "Ankh Eco Textiles",
            "name": "Royal Cotton Velvet",
            "in_stock": True,
            "gallery": ["https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800"],
            "description": "Luxuriously soft cotton velvet with a rich pile and deep sheen, suitable for evening wear and upholstery.",
            "price_amount": 26.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 280,
            "breathability_rating": 2,
            "is_hypoallergenic": True,
            "texture_smoothness": 5,
            "oeko_tex_certified": True,
            "recommended_climate": ["Temperate", "Polar"]
        },
        {
            "id": "cashmere-fabric-prod",
            "brand": "Ankh Eco Textiles",
            "name": "Ultra-Soft Cashmere Twill",
            "in_stock": True,
            "gallery": ["https://images.unsplash.com/photo-1551232864-3f0890e580d9?w=800"],
            "description": "Extremely soft and lightweight pure cashmere twill fabric. Unbelievably comfortable and warm.",
            "price_amount": 65.00,
            "currency_symbol": "$",
            "supplier_id": supplier.id,
            "gsm": 180,
            "breathability_rating": 4,
            "is_hypoallergenic": True,
            "texture_smoothness": 5,
            "oeko_tex_certified": True,
            "recommended_climate": ["Polar", "Temperate"]
        }
    ]

    category_ids = {c.name: c.id for c in db.query(models.Category).all()}

    for p in products:
        existing = db.query(models.Product).filter(models.Product.id == p["id"]).first()
        category_id = category_ids.get(PRODUCT_CATEGORIES.get(p["id"]))
        if not existing:
            db.add(models.Product(**p, category_id=category_id))
        elif existing.category_id is None:
            # Backfill for databases seeded before products had a category.
            existing.category_id = category_id

    db.commit()
    print("Database seeding completed.")
