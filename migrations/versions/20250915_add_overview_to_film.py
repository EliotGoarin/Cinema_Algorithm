"""create genre and film_genre tables

Revision ID: 20250915_add_genres_tables
Revises: 20250915_add_overview_to_film  # remplace par TON dernier revision id
Create Date: 2025-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "20250915_add_genres_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # table genre
    if not op.get_bind().dialect.has_table(op.get_bind(), "genre"):
        op.create_table(
            "genre",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("tmdb_id", sa.Integer, nullable=True, unique=True),
            sa.Column("name", sa.String(128), nullable=False, unique=True),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )

    # table d'association film_genre
    if not op.get_bind().dialect.has_table(op.get_bind(), "film_genre"):
        op.create_table(
            "film_genre",
            sa.Column("film_tmdb_id", sa.Integer, nullable=False, index=True),
            sa.Column("genre_id", sa.Integer, nullable=False, index=True),
            sa.PrimaryKeyConstraint("film_tmdb_id", "genre_id"),
            sa.ForeignKeyConstraint(["film_tmdb_id"], ["film.tmdb_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["genre_id"], ["genre.id"], ondelete="CASCADE"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_0900_ai_ci",
        )

def downgrade():
    # ordre inverse
    try:
        op.drop_table("film_genre")
    except Exception:
        pass
    try:
        op.drop_table("genre")
    except Exception:
        pass
