"""empty message

Revision ID: 24e217636bf2
Revises: a9732fc583f7
Create Date: 2023-10-23 15:41:44.119155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24e217636bf2'
down_revision: Union[str, None] = 'a9732fc583f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('report', 'freq',
               existing_type=sa.VARCHAR(length=2),
               type_=sa.String(length=16),
               existing_nullable=False)
    op.drop_column('report', 'periods')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('report', sa.Column('periods', sa.INTEGER(), autoincrement=False, nullable=False))
    op.alter_column('report', 'freq',
               existing_type=sa.String(length=16),
               type_=sa.VARCHAR(length=2),
               existing_nullable=False)
    # ### end Alembic commands ###
