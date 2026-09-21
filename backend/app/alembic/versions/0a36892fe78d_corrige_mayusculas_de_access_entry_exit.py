"""corrige mayusculas de access entry exit

Revision ID: 0a36892fe78d
Revises: 197b58b0a634
Create Date: 2026-09-20 20:35:13.809219

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '0a36892fe78d'
down_revision = '197b58b0a634'
branch_labels = None
depends_on = None


def upgrade():
    # La migración anterior agregó 'access_entry'/'access_exit' en minúscula,
    # pero SQLAlchemy serializa un StrEnum de Python usando el NOMBRE del
    # miembro (mayúsculas), no su valor — igual que el resto de las columnas
    # de este mismo enum (PAYMENT_CREATED, etc). Se agregan las etiquetas
    # correctas; las dos en minúscula quedan sin uso (Postgres no permite
    # quitar valores de un enum).
    op.execute("COMMIT")
    op.execute("ALTER TYPE parkinglogaction ADD VALUE IF NOT EXISTS 'ACCESS_ENTRY'")
    op.execute("ALTER TYPE parkinglogaction ADD VALUE IF NOT EXISTS 'ACCESS_EXIT'")


def downgrade():
    pass
