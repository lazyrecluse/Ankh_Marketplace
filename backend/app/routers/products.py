import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, serializers
from ..database import get_db

router = APIRouter(tags=["Products"])

# backend/app/static/uploads
UPLOADS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads"
)
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    file_url = f"/static/uploads/{filename}"
    return {"url": file_url, "image_url": file_url}


@router.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).all()
    return [{"name": c.name} for c in categories]


@router.get("/api/currencies")
def get_currencies(db: Session = Depends(get_db)):
    currencies = db.query(models.Currency).all()
    return [{"label": c.label, "symbol": c.symbol} for c in currencies]


@router.get("/api/products")
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
        # Was: id LIKE '<cat>%' OR name LIKE '%<cat>%'. Products now carry a
        # real category_id, so this is an ordinary join.
        query = query.join(models.Category).filter(
            models.Category.name == category.lower()
        )

    if search:
        query = query.filter(
            models.Product.name.like(f"%{search}%") |
            models.Product.brand.like(f"%{search}%") |
            models.Product.description.like(f"%{search}%")
        )

    if sensitive_skin:
        # Plain boolean column — no reason for this to have been a Python-side
        # filter over the full table.
        query = query.filter(models.Product.is_hypoallergenic.is_(True))

    products = query.all()
    currencies = serializers.load_currencies(db)

    # `climate` stays in Python: it reads a JSON list, and the SQL for that is
    # dialect-specific (SQLite json_each vs Postgres containment). The catalog
    # is small enough that this is not worth the portability cost. Revisit if
    # it grows.
    results = []
    for p in products:
        if climate and climate.lower() != "all":
            climates = [c.lower() for c in (p.recommended_climate or [])]
            if climate.lower() not in climates and "all" not in climates:
                continue
        results.append(serializers.product_to_json(p, currencies))

    return results


@router.get("/api/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    return serializers.product_to_json(p, serializers.load_currencies(db))
