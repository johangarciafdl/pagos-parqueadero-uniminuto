"""invitados con documento y fix borrado de vehiculo

Revision ID: 04b04af04bc0
Revises: 0a36892fe78d
Create Date: 2026-09-21 19:27:51.108077

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '04b04af04bc0'
down_revision = '0a36892fe78d'
branch_labels = None
depends_on = None


def upgrade():
    # Antes, borrar un vehiculo con pagos asociados fallaba con un error de
    # integridad referencial (la FK no tenia ondelete). Con SET NULL, el
    # pago conserva su historial pero queda sin vehiculo asociado.
    op.drop_constraint(op.f('payment_vehicle_id_fkey'), 'payment', type_='foreignkey')
    op.create_foreign_key(
        'payment_vehicle_id_fkey', 'payment', 'vehicle', ['vehicle_id'], ['id'],
        ondelete='SET NULL',
    )
    document_type_enum = sa.Enum('CC', 'CE', 'TI', 'PASAPORTE', name='documenttype')
    document_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('user', sa.Column('document_type', document_type_enum, nullable=True))


def downgrade():
    op.drop_column('user', 'document_type')
    sa.Enum(name='documenttype').drop(op.get_bind(), checkfirst=True)
    op.drop_constraint('payment_vehicle_id_fkey', 'payment', type_='foreignkey')
    op.create_foreign_key(op.f('payment_vehicle_id_fkey'), 'payment', 'vehicle', ['vehicle_id'], ['id'])
