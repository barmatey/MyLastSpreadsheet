"""empty message

Revision ID: c961fd5aa337
Revises: 5de6c02e9d4c
Create Date: 2023-10-18 11:01:59.736826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c961fd5aa337'
down_revision: Union[str, None] = '5de6c02e9d4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('group')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group',
    sa.Column('title', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('source_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('sheet_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('plan_items', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['sheet_id'], ['sheet.id'], name='group_sheet_id_fkey'),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name='group_source_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='group_pkey')
    )
    # ### end Alembic commands ###
