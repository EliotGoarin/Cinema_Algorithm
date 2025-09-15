"""add overview to film

Revision ID: 20250915_add_overview_to_film
Revises: <PUT_PREVIOUS_REVISION_ID_HERE>
Create Date: 2025-09-15

"""
from alembic import op
import sqlalchemy as sa


# Références de révision
revision = "20250915_add_overview_to_film"
down_revision = "<PUT_PREVIOUS_REVISION_ID_HERE>"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("film") as batch_op:
        batch_op.add_column(sa.Column("overview", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("film") as batch_op:
        batch_op.drop_column("overview")
