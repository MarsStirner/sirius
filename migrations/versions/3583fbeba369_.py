"""empty message

Revision ID: 3583fbeba369
Revises: 970aa6314176
Create Date: 2016-11-22 17:56:46.478000

"""

# revision identifiers, used by Alembic.
revision = '3583fbeba369'
down_revision = '970aa6314176'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('host',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.Column('system_id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=80), nullable=False),
    sa.ForeignKeyConstraint(['system_id'], ['system.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', 'system_id', name='_host_uc')
    )
    op.create_index(op.f('ix_host_system_id'), 'host', ['system_id'], unique=False)
    op.add_column(u'api_method', sa.Column('host_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_api_method_host_id'), 'api_method', ['host_id'], unique=False)
    op.create_foreign_key(None, 'api_method', 'host', ['host_id'], ['id'])
    op.drop_column(u'system', 'host')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'system', sa.Column('host', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'api_method', type_='foreignkey')
    op.drop_index(op.f('ix_api_method_host_id'), table_name='api_method')
    op.drop_column(u'api_method', 'host_id')
    op.drop_index(op.f('ix_host_system_id'), table_name='host')
    op.drop_table('host')
    ### end Alembic commands ###
