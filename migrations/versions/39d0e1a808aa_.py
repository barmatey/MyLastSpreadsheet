"""empty message

Revision ID: 39d0e1a808aa
Revises: f7ffcad8522e
Create Date: 2023-11-04 11:28:58.837734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39d0e1a808aa'
down_revision: Union[str, None] = 'f7ffcad8522e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('formula', sa.Column('cell_id', sa.Uuid(), nullable=False))
    op.create_foreign_key(None, 'formula', 'cell', ['cell_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'formula', type_='foreignkey')
    op.drop_column('formula', 'cell_id')
    # ### end Alembic commands ###