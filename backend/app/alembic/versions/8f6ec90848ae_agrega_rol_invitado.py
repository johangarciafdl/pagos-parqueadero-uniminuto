"""agrega rol invitado

Revision ID: 8f6ec90848ae
Revises: bdb27a1f4765
Create Date: 2026-09-20 19:50:40.807083

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '8f6ec90848ae'
down_revision = 'bdb27a1f4765'
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE ... ADD VALUE no puede ejecutarse dentro de la misma
    # transacción que Alembic abre por defecto en Postgres; se cierra esa
    # transacción primero para que corra en modo autocommit.
    op.execute("COMMIT")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'INVITADO'")


def downgrade():
    # Postgres no soporta quitar un valor de un enum directamente; no hay
    # downgrade seguro sin recrear el tipo. Se deja como no-op.
    pass
