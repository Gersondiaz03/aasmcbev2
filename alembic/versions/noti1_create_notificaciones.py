"""create notificaciones table

Revision ID: noti1
Revises: 81bd4af25701
Create Date: 2025-05-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'noti1'
down_revision = '81bd4af25701'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'Notificaciones',
        sa.Column('id_notificacion', sa.Integer, primary_key=True, index=True),
        sa.Column('id_estudiante', sa.Integer, sa.ForeignKey('Usuarios.id_usuario'), nullable=True),
        sa.Column('id_psicologo', sa.Integer, sa.ForeignKey('Usuarios.id_usuario'), nullable=True),
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('leida', sa.Boolean, default=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

def downgrade():
    op.drop_table('Notificaciones')
