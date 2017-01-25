"""empty message

Revision ID: b549ae010432
Revises: a1230e791a22
Create Date: 2017-01-25 16:13:41.769000

"""

# revision identifiers, used by Alembic.
revision = 'b549ae010432'
down_revision = 'a1230e791a22'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entity_image', sa.Column('root_entity_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_entity_image_root_entity_id'), 'entity_image', ['root_entity_id'], unique=False)
    op.create_foreign_key(None, 'entity_image', 'entity', ['root_entity_id'], ['id'])
    op.add_column('entity_image_diff', sa.Column('root_entity_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_entity_image_diff_root_entity_id'), 'entity_image_diff', ['root_entity_id'], unique=False)
    op.create_foreign_key(None, 'entity_image_diff', 'entity', ['root_entity_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'entity_image_diff', type_='foreignkey')
    op.drop_index(op.f('ix_entity_image_diff_root_entity_id'), table_name='entity_image_diff')
    op.drop_column('entity_image_diff', 'root_entity_id')
    op.drop_constraint(None, 'entity_image', type_='foreignkey')
    op.drop_index(op.f('ix_entity_image_root_entity_id'), table_name='entity_image')
    op.drop_column('entity_image', 'root_entity_id')
    ### end Alembic commands ###
