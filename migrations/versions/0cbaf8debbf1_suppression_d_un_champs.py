"""Suppression d'un champs

Revision ID: 0cbaf8debbf1
Revises: 05dc5d794194
Create Date: 2025-05-08 16:17:45.107661

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cbaf8debbf1'
down_revision = '05dc5d794194'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('test_field')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('test_field', sa.VARCHAR(length=50), autoincrement=False, nullable=True))

    # ### end Alembic commands ###
