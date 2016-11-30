"""empty message

Revision ID: 6e2568473447
Revises: 464fe70376fe
Create Date: 2016-11-29 22:12:43.535000

"""

# revision identifiers, used by Alembic.
revision = '6e2568473447'
down_revision = '464fe70376fe'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entity_image', sa.Column('created', sa.DateTime(), server_default='now()', nullable=False))
    op.add_column('entity_image', sa.Column('modified', sa.DateTime(), server_default='now()', nullable=False))
    op.add_column('matching_id', sa.Column('created', sa.DateTime(), server_default='now()', nullable=False))
    op.add_column('sch_group_request', sa.Column('enabled', sa.Boolean(), server_default='false', nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sch_group_request', 'enabled')
    op.drop_column('matching_id', 'created')
    op.drop_column('entity_image', 'modified')
    op.drop_column('entity_image', 'created')
    ### end Alembic commands ###