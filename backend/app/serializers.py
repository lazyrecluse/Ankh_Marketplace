"""JSON shaping for API responses.

Extracted because the product payload was previously built inline in three
places — GET /api/products, GET /api/products/{id}, and the supplier
dashboard's inventory_alerts — and had drifted between them.

Two things that used to be fabricated here are gone:

* Prices are computed from ``Currency.rate_to_usd`` instead of the hardcoded
  0.92 / 0.79 multipliers that ``build_product_prices`` used to apply.

* The hardcoded Size S/M/L ``attributes`` block has been removed. It never
  described fabric; it existed only so that ProductCard and DescriptionPage
  would not crash on a missing key. The key is still emitted as an empty list,
  because both of those components branch on ``attributes?.length > 0`` and
  already have a correct no-attributes path.
"""

from typing import Sequence

from sqlalchemy.orm import Session

from . import models


def load_currencies(db: Session) -> list[models.Currency]:
    """Currencies in a stable order (USD, EUR, GBP as seeded).

    Callers should load these ONCE per request and pass them down — doing it
    inside a per-product loop is an N+1 query.
    """
    return db.query(models.Currency).order_by(models.Currency.id).all()


def build_product_prices(
    base_amount: float, currencies: Sequence[models.Currency]
) -> list[dict]:
    return [
        {
            "currency": {"label": c.label, "symbol": c.symbol},
            "amount": round(float(base_amount) * c.rate_to_usd, 2),
        }
        for c in currencies
    ]


def product_to_json(
    product: models.Product, currencies: Sequence[models.Currency]
) -> dict:
    """The shape the React store components consume."""
    return {
        "id": product.id,
        "brand": product.brand,
        "name": product.name,
        "inStock": product.in_stock,
        "gallery": product.gallery or [],
        "description": product.description,
        "prices": build_product_prices(product.price_amount, currencies),
        # See module docstring — intentionally always empty.
        "attributes": [],
        "category": product.category.name if product.category else None,
        "gsm": product.gsm,
        "breathability_rating": product.breathability_rating,
        "is_hypoallergenic": product.is_hypoallergenic,
        "texture_smoothness": product.texture_smoothness,
        "oeko_tex_certified": product.oeko_tex_certified,
        "recommended_climate": product.recommended_climate or [],
    }
