import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/supplier", tags=["Supplier"])


def _category_guess(db: Session, name: str, slug: str) -> Optional[int]:
    """Best-effort category when the supplier hasn't explicitly picked one."""
    haystack = f"{name} {slug}".lower()
    matches = [
        c for c in db.query(models.Category).filter(models.Category.name != "all").all()
        if c.name.lower() in haystack
    ]
    if not matches:
        return None
    return max(matches, key=lambda c: len(c.name)).id


@router.get("/dashboard", response_model=schemas.SupplierDashboardOut)
def get_supplier_dashboard(
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
    products = db.query(models.Product).filter(models.Product.supplier_id == current_user.id).all()
    total_products = len(products)
    active_products = sum(1 for p in products if p.in_stock)

    product_ids = [p.id for p in products]

    supplier_order_items = db.query(models.OrderItem).filter(models.OrderItem.product_id.in_(product_ids)).all()
    order_ids = list(set([item.order_id for item in supplier_order_items]))

    orders = db.query(models.Order).filter(models.Order.id.in_(order_ids)).order_by(models.Order.created_at.desc()).all()

    pending_orders = sum(1 for o in orders if o.status == "Pending")

    # Inventory alert: anything not in stock.
    inventory_alerts = [p for p in products if not p.in_stock]

    return {
        "total_products": total_products,
        "active_products": active_products,
        "pending_orders": pending_orders,
        "recent_orders": orders[:5],
        "inventory_alerts": inventory_alerts
    }


@router.get("/orders")
def get_supplier_orders(
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
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


@router.put("/orders/{order_id}/status")
def update_supplier_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
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


@router.post("/products")
def add_supplier_product(
    product_data: schemas.ProductCreate,
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
    # Resolve brand name from onboarding details
    profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == current_user.id).first()
    brand_name = product_data.brand or (profile.business_name if (profile and profile.business_name) else "Ankh Supplier")

    # Generate unique slug if not provided
    if product_data.id:
        slug = product_data.id
    else:
        base_slug = f"{product_data.name} {brand_name}".lower()
        base_slug = re.sub(r'[^a-z0-9]+', '-', base_slug).strip('-')
        slug = base_slug

        for _attempt in range(10):
            if db.query(models.Product).filter(models.Product.id == slug).first() is None:
                break
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        else:
            raise HTTPException(
                status_code=500, detail="Could not generate a unique product id"
            )

    db_product = db.query(models.Product).filter(models.Product.id == slug).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product ID already exists")

    new_prod = models.Product(
        id=slug,
        brand=brand_name,
        name=product_data.name,
        in_stock=product_data.in_stock,
        gallery=product_data.gallery or [],
        description=product_data.description,
        price_amount=product_data.price_amount,
        currency_symbol=product_data.currency_symbol,
        supplier_id=current_user.id,
        category_id=product_data.category_id or _category_guess(db, product_data.name, slug),
        gsm=product_data.gsm,
        breathability_rating=product_data.breathability_rating,
        is_hypoallergenic=product_data.is_hypoallergenic,
        texture_smoothness=product_data.texture_smoothness,
        oeko_tex_certified=product_data.oeko_tex_certified,
        recommended_climate=product_data.recommended_climate or []
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return {"status": "success", "message": "Product created successfully"}


@router.put("/products/{product_id}")
def update_supplier_product(
    product_id: str,
    product_data: schemas.ProductCreate,
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
    prod = db.query(models.Product).filter(models.Product.id == product_id, models.Product.supplier_id == current_user.id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found or not owned by supplier")

    profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == current_user.id).first()
    brand_name = product_data.brand or (profile.business_name if (profile and profile.business_name) else "Ankh Supplier")

    prod.brand = brand_name
    prod.name = product_data.name
    prod.in_stock = product_data.in_stock
    if product_data.gallery is not None:
        prod.gallery = product_data.gallery
    prod.description = product_data.description
    prod.price_amount = product_data.price_amount
    prod.currency_symbol = product_data.currency_symbol
    if product_data.category_id is not None:
        prod.category_id = product_data.category_id
    elif prod.category_id is None:
        prod.category_id = _category_guess(db, product_data.name, prod.id)
    prod.gsm = product_data.gsm
    prod.breathability_rating = product_data.breathability_rating
    prod.is_hypoallergenic = product_data.is_hypoallergenic
    prod.texture_smoothness = product_data.texture_smoothness
    prod.oeko_tex_certified = product_data.oeko_tex_certified
    prod.recommended_climate = product_data.recommended_climate or []

    db.commit()
    return {"status": "success", "message": "Product updated successfully"}


@router.delete("/products/{product_id}")
def delete_supplier_product(
    product_id: str,
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
    prod = db.query(models.Product).filter(models.Product.id == product_id, models.Product.supplier_id == current_user.id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found or not owned by supplier")

    referencing_items = db.query(models.OrderItem).filter(models.OrderItem.product_id == product_id).count()
    if referencing_items:
        raise HTTPException(
            status_code=409,
            detail="Product appears on existing orders and cannot be deleted. Mark it out of stock instead.",
        )

    db.delete(prod)
    db.commit()
    return {"status": "success", "message": "Product deleted successfully"}
