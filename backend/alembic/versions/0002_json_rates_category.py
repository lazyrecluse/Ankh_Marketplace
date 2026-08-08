"""json columns, currency rates, product category FK

Three changes, none of which alter existing data semantics:

1. gallery / recommended_climate / skin_preferences / categories move from
   Text to JSON. SQLite serializes JSON as TEXT with the same encoding the old
   json.dumps() calls produced, so stored rows are already valid and no data
   conversion is required. This is a type annotation change only.

2. currencies gains rate_to_usd, backfilled with the 0.92 / 0.79 constants that
   were hardcoded in build_product_prices() so prices do not move.

3. products gains category_id, backfilled by matching the product's slug prefix
   against category names — which is exactly what the old
   `id LIKE 'cotton%'` filter was approximating, just done once here instead of
   on every request.

Revision ID: 0002_json_rates_category
Revises: 0001_baseline
Create Date: 2026-08-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_json_rates_category"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Matches the values previously hardcoded in build_product_prices().
_SEED_RATES = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79}


def upgrade() -> None:
    # --- 1. Text -> JSON -----------------------------------------------------
    with op.batch_alter_table("products") as batch:
        batch.alter_column(
            "gallery", existing_type=sa.Text(), type_=sa.JSON(), existing_nullable=False
        )
        batch.alter_column(
            "recommended_climate",
            existing_type=sa.Text(),
            type_=sa.JSON(),
            existing_nullable=True,
        )

    with op.batch_alter_table("buyer_profiles") as batch:
        batch.alter_column(
            "skin_preferences",
            existing_type=sa.Text(),
            type_=sa.JSON(),
            existing_nullable=True,
        )

    with op.batch_alter_table("supplier_profiles") as batch:
        batch.alter_column(
            "categories", existing_type=sa.Text(), type_=sa.JSON(), existing_nullable=True
        )

    # --- 2. currency rates ---------------------------------------------------
    with op.batch_alter_table("currencies") as batch:
        batch.add_column(
            sa.Column(
                "rate_to_usd", sa.Float(), nullable=False, server_default=sa.text("1.0")
            )
        )

    currencies = sa.table(
        "currencies", sa.column("label", sa.String), sa.column("rate_to_usd", sa.Float)
    )
    for label, rate in _SEED_RATES.items():
        op.execute(
            currencies.update()
            .where(currencies.c.label == op.inline_literal(label))
            .values(rate_to_usd=rate)
        )

    # --- 3. product category -------------------------------------------------
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_products_category_id", "categories", ["category_id"], ["id"]
        )
        batch.create_index("ix_products_category_id", ["category_id"])

    # Backfill: a product whose slug starts with a category name belongs to it.
    # "all" is the catch-all UI tile, not a real category, so it is excluded.
    op.execute(
        """
        UPDATE products
           SET category_id = (
               SELECT c.id
                 FROM categories c
                WHERE c.name <> 'all'
                  AND products.id LIKE c.name || '%'
                ORDER BY LENGTH(c.name) DESC
                LIMIT 1
           )
         WHERE category_id IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.drop_index("ix_products_category_id")
        batch.drop_constraint("fk_products_category_id", type_="foreignkey")
        batch.drop_column("category_id")

    with op.batch_alter_table("currencies") as batch:
        batch.drop_column("rate_to_usd")

    with op.batch_alter_table("supplier_profiles") as batch:
        batch.alter_column(
            "categories", existing_type=sa.JSON(), type_=sa.Text(), existing_nullable=True
        )

    with op.batch_alter_table("buyer_profiles") as batch:
        batch.alter_column(
            "skin_preferences",
            existing_type=sa.JSON(),
            type_=sa.Text(),
            existing_nullable=True,
        )

    with op.batch_alter_table("products") as batch:
        batch.alter_column(
            "recommended_climate",
            existing_type=sa.JSON(),
            type_=sa.Text(),
            existing_nullable=True,
        )
        batch.alter_column(
            "gallery", existing_type=sa.JSON(), type_=sa.Text(), existing_nullable=False
        )
