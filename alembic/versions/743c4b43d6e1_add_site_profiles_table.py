"""add site_profiles table"""

revision = '743c4b43d6e1'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table('site_profiles',
    sa.Column('domain', sa.String(), nullable=False),
    sa.Column('last_successful_strategy', sa.String(), nullable=True),
    sa.Column('success_count', sa.Integer(), nullable=False),
    sa.Column('failure_count', sa.Integer(), nullable=False),
    sa.Column('consecutive_failures', sa.Integer(), nullable=False),
    sa.Column('error_threshold', sa.Integer(), nullable=False),
    sa.Column('avg_confidence', sa.Float(), nullable=True),
    sa.Column('last_attempted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_succeeded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('strategy_history', sa.JSON(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_site_profiles'))
    )
    op.create_index(op.f('ix_site_profiles_domain'), 'site_profiles', ['domain'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_index(op.f('ix_site_profiles_domain'), table_name='site_profiles')
    op.drop_table('site_profiles')
    # ### end Alembic commands ###