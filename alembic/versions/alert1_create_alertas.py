"""create alertas table

Revision ID: alert1
Revises: noti1
Create Date: 2025-09-15
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "alert1"
down_revision = "3868d0d804c7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "Alertas",
        sa.Column("id_alerta", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "id_estudiante",
            sa.Integer,
            sa.ForeignKey("Usuarios.id_usuario"),
            nullable=False,
        ),
        sa.Column("texto", sa.String(), nullable=False),
        sa.Column(
            "severidad", sa.String(length=20), nullable=False, server_default="ALTA"
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )


def downgrade():
    op.drop_table("Alertas")
