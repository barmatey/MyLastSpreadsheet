"""empty message

Revision ID: 856727e29c18
Revises: 8bbe21d9e5ee
Create Date: 2023-10-29 11:16:30.963007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '856727e29c18'
down_revision: Union[str, None] = '8bbe21d9e5ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cell', sa.Column('background', sa.String(length=21), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cell', 'background')
    # ### end Alembic commands ###