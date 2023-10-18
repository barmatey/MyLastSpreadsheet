"""empty message

Revision ID: 0af5a5cc0735
Revises: c99a8a75cdd7
Create Date: 2023-10-18 18:49:57.637508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0af5a5cc0735'
down_revision: Union[str, None] = 'c99a8a75cdd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('report', 'sheet_id',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.String(length=64),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('report', 'sheet_id',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=32),
               existing_nullable=False)
    # ### end Alembic commands ###
