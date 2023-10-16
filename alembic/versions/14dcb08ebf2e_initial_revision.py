"""initial revision

Revision ID: 14dcb08ebf2e
Revises:
Create Date: 2023-10-15 21:13:49.716003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14dcb08ebf2e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('guilds',
    sa.Column('guild_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('guild_id')
    )
    op.create_table('reminders',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('channel_id', sa.BigInteger(), nullable=False),
    sa.Column('message_id', sa.BigInteger(), nullable=False),
    sa.Column('author_id', sa.BigInteger(), nullable=False),
    sa.Column('mention_ids', sa.ARRAY(sa.BigInteger()), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('expiration', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reminders')
    op.drop_table('guilds')
    # ### end Alembic commands ###