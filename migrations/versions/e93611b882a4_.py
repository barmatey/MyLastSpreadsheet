"""empty message

Revision ID: e93611b882a4
Revises: 3edf6c6dc4b0
Create Date: 2023-10-27 15:46:59.919091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e93611b882a4'
down_revision: Union[str, None] = '3edf6c6dc4b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'publisher', ['key'])
    op.create_unique_constraint(None, 'subscriber', ['key'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'subscriber', type_='unique')
    op.drop_constraint(None, 'publisher', type_='unique')
    # ### end Alembic commands ###