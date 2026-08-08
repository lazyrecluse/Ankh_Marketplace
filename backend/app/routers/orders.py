from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(tags=["Orders"])


@router.post("/api/orders")
def place_order(
    order_data: schemas.OrderCreate,
    current_user: models.User = Depends(security.require_buyer),
    db: Session = Depends(get_db),
):
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


@router.get("/api/buyer/orders")
def get_buyer_orders(
    current_user: models.User = Depends(security.require_buyer),
    db: Session = Depends(get_db),
):
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
