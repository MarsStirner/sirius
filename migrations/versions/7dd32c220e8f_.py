"""empty message

Revision ID: 7dd32c220e8f
Revises: 9bf5c4d116af
Create Date: 2016-11-07 19:43:14.851000

"""

# revision identifiers, used by Alembic.
revision = '7dd32c220e8f'
down_revision = '9bf5c4d116af'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'entity_image', sa.Column('level', sa.Integer(), nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'entity_image', 'level')
    ### end Alembic commands ###