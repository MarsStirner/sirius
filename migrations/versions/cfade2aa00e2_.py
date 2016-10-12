"""empty message

Revision ID: cfade2aa00e2
Revises: d8f28476d08a
Create Date: 2016-10-11 20:00:27.966000

"""

# revision identifiers, used by Alembic.
revision = 'cfade2aa00e2'
down_revision = 'd8f28476d08a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('operation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('protocol',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('system',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.Column('url', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('entity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.Column('system_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['system_id'], ['system.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('system_id', 'code', name='_sys_entity_uc')
    )
    op.add_column(u'api_method', sa.Column('entity_id', sa.Integer(), nullable=False))
    op.add_column(u'api_method', sa.Column('operation_id', sa.Integer(), nullable=False))
    op.add_column(u'api_method', sa.Column('protocol_id', sa.Integer(), nullable=False))
    op.create_unique_constraint('_entity_operation_uc', 'api_method', ['entity_id', 'operation_id'])
    op.drop_constraint(u'_entity_operation_system_uc', 'api_method', type_='unique')
    op.create_foreign_key(None, 'api_method', 'protocol', ['protocol_id'], ['id'])
    op.create_foreign_key(None, 'api_method', 'entity', ['entity_id'], ['id'])
    op.create_foreign_key(None, 'api_method', 'operation', ['operation_id'], ['id'])
    op.drop_column(u'api_method', 'entity_code')
    op.drop_column(u'api_method', 'operation_code')
    op.drop_column(u'api_method', 'system_code')
    op.add_column(u'matching_id', sa.Column('local_entity_id', sa.Integer(), nullable=False))
    op.add_column(u'matching_id', sa.Column('remote_entity_id', sa.Integer(), nullable=False))
    op.create_unique_constraint('_remote_entity_id_uc', 'matching_id', ['remote_entity_id', 'remote_id'])
    op.create_index(op.f('ix_matching_id_local_id'), 'matching_id', ['local_id'], unique=False)
    op.create_index(op.f('ix_matching_id_remote_id'), 'matching_id', ['remote_id'], unique=False)
    op.drop_constraint(u'_local_entity_id_uc', 'matching_id', type_='unique')
    op.create_unique_constraint('_local_entity_id_uc', 'matching_id', ['local_entity_id', 'local_id'])
    op.drop_constraint(u'_remote_sys_entity_id_uc', 'matching_id', type_='unique')
    op.create_foreign_key(None, 'matching_id', 'entity', ['remote_entity_id'], ['id'])
    op.create_foreign_key(None, 'matching_id', 'entity', ['local_entity_id'], ['id'])
    op.drop_column(u'matching_id', 'remote_entity_code')
    op.drop_column(u'matching_id', 'remote_sys_code')
    op.drop_column(u'matching_id', 'local_entity_code')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'matching_id', sa.Column('local_entity_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.add_column(u'matching_id', sa.Column('remote_sys_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.add_column(u'matching_id', sa.Column('remote_entity_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'matching_id', type_='foreignkey')
    op.drop_constraint(None, 'matching_id', type_='foreignkey')
    op.create_unique_constraint(u'_remote_sys_entity_id_uc', 'matching_id', ['remote_sys_code', 'remote_entity_code', 'remote_id'])
    op.drop_constraint('_local_entity_id_uc', 'matching_id', type_='unique')
    op.create_unique_constraint(u'_local_entity_id_uc', 'matching_id', ['local_entity_code', 'local_id'])
    op.drop_index(op.f('ix_matching_id_remote_id'), table_name='matching_id')
    op.drop_index(op.f('ix_matching_id_local_id'), table_name='matching_id')
    op.drop_constraint('_remote_entity_id_uc', 'matching_id', type_='unique')
    op.drop_column(u'matching_id', 'remote_entity_id')
    op.drop_column(u'matching_id', 'local_entity_id')
    op.add_column(u'api_method', sa.Column('system_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.add_column(u'api_method', sa.Column('operation_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.add_column(u'api_method', sa.Column('entity_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'api_method', type_='foreignkey')
    op.drop_constraint(None, 'api_method', type_='foreignkey')
    op.drop_constraint(None, 'api_method', type_='foreignkey')
    op.create_unique_constraint(u'_entity_operation_system_uc', 'api_method', ['entity_code', 'operation_code', 'system_code'])
    op.drop_constraint('_entity_operation_uc', 'api_method', type_='unique')
    op.drop_column(u'api_method', 'protocol_id')
    op.drop_column(u'api_method', 'operation_id')
    op.drop_column(u'api_method', 'entity_id')
    op.drop_table('entity')
    op.drop_table('system')
    op.drop_table('protocol')
    op.drop_table('operation')
    ### end Alembic commands ###
