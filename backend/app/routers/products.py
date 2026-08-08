import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
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
    # rate_to_usd is exposed so the frontend can convert a price filter typed in
    # the currently displayed currency back into the USD base that
    # Product.price_amount (and therefore min_price/max_price) is stored in.
    return [
        {"label": c.label, "symbol": c.symbol, "rate_to_usd": c.rate_to_usd}
        for c in db.query(models.Currency).all()
    ]


# Column each `sort` value maps to. Anything not in here is ignored rather than
# raising, so a stale bookmark with ?sort=whatever still returns the catalog.
_SORT_OPTIONS = {
    "price_asc": models.Product.price_amount.asc(),
    "price_desc": models.Product.price_amount.desc(),
    "name_asc": models.Product.name.asc(),
    "name_desc": models.Product.name.desc(),
}


def _like_term(term: str) -> str:
    """Escape LIKE wildcards so a search for "50%" is not a match-everything.

    Paired with ``escape="\\"`` at the call site. Without this, `%` and `_`
    typed by a user are treated as pattern syntax.
    """
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/api/products")
def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    climate: Optional[str] = None,
    sensitive_skin: Optional[bool] = None,
    supplier_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price, in USD"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price, in USD"),
    in_stock: Optional[bool] = None,
    sort: Optional[str] = Query(
        None,
        description="One of price_asc, price_desc, name_asc, name_desc.",
    ),
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

    if search and search.strip():
        # ilike, not like: LIKE is case-sensitive on Postgres (the docker-compose
        # target), so a lowercase query matched nothing there while appearing to
        # work on SQLite, where LIKE folds ASCII case.
        term = _like_term(search.strip())
        query = query.filter(
            models.Product.name.ilike(term, escape="\\") |
            models.Product.brand.ilike(term, escape="\\") |
            models.Product.description.ilike(term, escape="\\")
        )

    if min_price is not None:
        query = query.filter(models.Product.price_amount >= min_price)

    if max_price is not None:
        query = query.filter(models.Product.price_amount <= max_price)

    if in_stock:
        query = query.filter(models.Product.in_stock.is_(True))

    if sensitive_skin:
        # Plain boolean column — no reason for this to have been a Python-side
        # filter over the full table.
        query = query.filter(models.Product.is_hypoallergenic.is_(True))

    if sort in _SORT_OPTIONS:
        query = query.order_by(_SORT_OPTIONS[sort])

    products = query.all()
    currencies = serializers.load_currencies(db)

    # `climate` stays in Python: it reads a JSON list, and the SQL for that is
    # dialect-specific (SQLite json_each vs Postgres containment). The catalog
    # is small enough that this is not worth the portability cost. Revisit if
    # it grows. Filtering preserves the SQL sort order applied above.
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
