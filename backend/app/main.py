"""Ankh B2B Textile Marketplace API — application entry point.

Run with:    cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
Migrations:  cd backend && .venv/bin/alembic upgrade head
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import seed
from .database import get_db
from .routers import auth, ai, onboarding, orders, products, supplier
from .security import settings

# ------------------------------------------------------------------ app setup
tags_metadata = [
    {"name": "Auth", "description": "Authentication, registration, login, and user profiles."},
    {"name": "Onboarding", "description": "Onboarding forms and profile completions for Buyers and Suppliers."},
    {"name": "Products", "description": "Catalog endpoints for categories, currencies, and products."},
    {"name": "Orders", "description": "Checkout and order placement operations for Buyers."},
    {"name": "Supplier", "description": "Supplier dashboard widgets, inventory CRUD, and order management."},
    {"name": "AI Assistant", "description": "AI-powered fabric recommendation chat endpoint."},
]

app = FastAPI(
    title="Ankh B2B Textile Marketplace API",
    description="Full B2B Textile marketplace API documenting Auth, Onboarding, Products, Orders, and Dashboards.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# CORS — origins driven by ANKH_ALLOWED_ORIGINS (defaults to localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ middleware

UPLOADS_DIR = products.UPLOADS_DIR  # avoid repeating the path
app.mount("/static/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        seed.seed_db_if_empty(db)
    finally:
        db.close()


# ------------------------------------------------------------------ routers

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(supplier.router)
app.include_router(ai.router)
