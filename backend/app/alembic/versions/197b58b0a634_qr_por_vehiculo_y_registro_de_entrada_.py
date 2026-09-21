"""qr por vehiculo y registro de entrada salida

Revision ID: 197b58b0a634
Revises: 8f6ec90848ae
Create Date: 2026-09-20 20:28:28.223182

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '197b58b0a634'
down_revision = '8f6ec90848ae'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE parkinglogaction ADD VALUE IF NOT EXISTS 'access_entry'")
    op.execute("ALTER TYPE parkinglogaction ADD VALUE IF NOT EXISTS 'access_exit'")


def downgrade():
    # Postgres no soporta quitar un valor de un enum directamente; no hay
    # downgrade seguro sin recrear el tipo. Se deja como no-op.
    pass
