"""Add department_id to positions table

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add department_id column to positions
    op.add_column('positions', sa.Column('department_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_position_department',
        'positions', 'departments',
        ['department_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for faster lookups
    op.create_index('idx_position_department_id', 'positions', ['department_id'])
    
    # Seed: assign existing positions to departments based on their codes
    conn = op.get_bind()
    
    # Engineering (id=1): SE001, SE002, TL001, EM001
    conn.execute(text("""
        UPDATE positions SET department_id = 1
        WHERE code IN ('SE001', 'SE002', 'TL001', 'EM001')
    """))
    
    # Human Resources (id=2): HR001, HR002
    conn.execute(text("""
        UPDATE positions SET department_id = 2
        WHERE code IN ('HR001', 'HR002')
    """))
    
    # Sales (id=3): SR001, SM001
    conn.execute(text("""
        UPDATE positions SET department_id = 3
        WHERE code IN ('SR001', 'SM001')
    """))
    
    # Marketing (id=4): MS001
    conn.execute(text("""
        UPDATE positions SET department_id = 4
        WHERE code IN ('MS001')
    """))
    
    # DIR001 is a cross-department role — leave NULL


def downgrade():
    op.drop_index('idx_position_department_id', table_name='positions')
    op.drop_constraint('fk_position_department', 'positions', type_='foreignkey')
    op.drop_column('positions', 'department_id')
