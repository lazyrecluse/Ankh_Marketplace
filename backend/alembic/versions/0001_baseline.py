"""baseline: current schema as of the pre-refactor models

Captures the schema that Base.metadata.create_all() was producing, so that
subsequent revisions have something to build on.

For a database that already exists (the developer's backend/ankh_marketplace.db),
do NOT run `upgrade` — the tables are already there. Stamp it instead:

    .venv/bin/alembic stamp 0001_baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"])
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)

    op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_currencies_id"), "currencies", ["id"])
    op.create_index(op.f("ix_currencies_label"), "currencies", ["label"], unique=True)

    op.create_table(
        "buyer_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("business_type", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("typical_order_qty", sa.String(), nullable=True),
        sa.Column("budget_range", sa.String(), nullable=True),
        sa.Column("preferred_climate", sa.String(), nullable=True),
        sa.Column("has_sensitive_skin", sa.Boolean(), nullable=True),
        sa.Column("skin_preferences", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_buyer_profiles_id"), "buyer_profiles", ["id"])

    op.create_table(
        "supplier_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("business_name", sa.String(), nullable=True),
        sa.Column("business_type", sa.String(), nullable=True),
        sa.Column("contact_info", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("operating_hours", sa.String(), nullable=True),
        sa.Column("categories", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_supplier_profiles_id"), "supplier_profiles", ["id"])

    op.create_table(
        "products",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("in_stock", sa.Boolean(), nullable=True),
        sa.Column("gallery", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_amount", sa.Float(), nullable=False),
        sa.Column("currency_symbol", sa.String(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("gsm", sa.Integer(), nullable=True),
        sa.Column("breathability_rating", sa.Integer(), nullable=True),
        sa.Column("is_hypoallergenic", sa.Boolean(), nullable=True),
        sa.Column("texture_smoothness", sa.Integer(), nullable=True),
        sa.Column("oeko_tex_certified", sa.Boolean(), nullable=True),
        sa.Column("recommended_climate", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("buyer_id", sa.Integer(), nullable=False),
        sa.Column("shipping_name", sa.String(), nullable=False),
        sa.Column("shipping_address", sa.String(), nullable=False),
        sa.Column("shipping_city", sa.String(), nullable=False),
        sa.Column("shipping_country", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("currency_symbol", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_id"), "orders", ["id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_amount", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_id"), "order_items", ["id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("supplier_profiles")
    op.drop_table("buyer_profiles")
    op.drop_table("currencies")
    op.drop_table("categories")
    op.drop_table("users")
