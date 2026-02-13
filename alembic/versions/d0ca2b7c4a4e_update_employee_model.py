"""Update Employee model

Revision ID: d0ca2b7c4a4e
Revises: 
Create Date: 2026-02-14 00:04:47.206891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0ca2b7c4a4e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('employees') as batch_op:
        batch_op.add_column(sa.Column('full_name', sa.String(length=100), nullable=True))  # Allow NULL initially
        batch_op.add_column(sa.Column('employee_code', sa.String(length=20), nullable=True))  # Allow NULL initially
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('position_id', sa.Integer(), nullable=True))
        # Skip dropping index if it doesn't exist
        try:
            batch_op.drop_index('ix_employees_name')
        except:
            pass
        batch_op.create_index('idx_employee_code', ['employee_code'], unique=False)
        batch_op.create_index('idx_employee_department', ['department_id'], unique=False)
        batch_op.create_index('idx_employee_email', ['email'], unique=False)
        batch_op.create_index('idx_employee_full_name', ['full_name'], unique=False)
        batch_op.create_index('idx_employee_position', ['position_id'], unique=False)
        batch_op.create_index('ix_employees_employee_code', ['employee_code'], unique=True)
        batch_op.create_index('ix_employees_full_name', ['full_name'], unique=False)
        batch_op.create_index('ix_employees_position_id', ['position_id'], unique=False)
        batch_op.create_foreign_key('fk_employee_position', 'positions', ['position_id'], ['id'], ondelete='SET NULL')
        
    # Copy data from name to full_name (if any existing data)
    op.execute("UPDATE employees SET full_name = name WHERE name IS NOT NULL AND full_name IS NULL")
    op.execute("UPDATE employees SET employee_code = 'EMP' || CAST(id AS TEXT) WHERE employee_code IS NULL")
        
    # Now make columns non-nullable and drop old column
    with op.batch_alter_table('employees') as batch_op:
        batch_op.alter_column('full_name', nullable=False)
        batch_op.alter_column('employee_code', nullable=False)
        # Only drop if column exists
        try:
            batch_op.drop_column('name')
        except:
            pass


def downgrade() -> None:
    with op.batch_alter_table('employees') as batch_op:
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=100), nullable=False))
        batch_op.drop_constraint('fk_employee_position', type_='foreignkey')
        batch_op.drop_index('ix_employees_position_id')
        batch_op.drop_index('ix_employees_full_name')
        batch_op.drop_index('ix_employees_employee_code')
        batch_op.drop_index('idx_employee_position')
        batch_op.drop_index('idx_employee_full_name')
        batch_op.drop_index('idx_employee_email')
        batch_op.drop_index('idx_employee_department')
        batch_op.drop_index('idx_employee_code')
        batch_op.create_index('ix_employees_name', ['name'], unique=False)
        batch_op.drop_column('position_id')
        batch_op.drop_column('phone')
        batch_op.drop_column('employee_code')
        batch_op.drop_column('full_name')
