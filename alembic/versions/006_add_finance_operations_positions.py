"""Add positions for Finance and Operations departments

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Finance (id=5) positions
    conn.execute(text("""
        INSERT INTO positions (title, code, level, description, department_id)
        VALUES 
            ('Financial Analyst', 'FIN001', 'JUNIOR', 'Analyzes financial data and prepares reports', 5),
            ('Senior Accountant', 'FIN002', 'SENIOR', 'Handles advanced accounting tasks', 5),
            ('Finance Manager', 'FIN003', 'MANAGER', 'Manages finance department operations', 5)
    """))
    
    # Operations (id=6) positions
    conn.execute(text("""
        INSERT INTO positions (title, code, level, description, department_id)
        VALUES 
            ('Operations Specialist', 'OPS001', 'JUNIOR', 'Handles day-to-day operations', 6),
            ('Operations Coordinator', 'OPS002', 'SENIOR', 'Coordinates team operations', 6),
            ('Operations Manager', 'OPS003', 'MANAGER', 'Manages operations department', 6)
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DELETE FROM positions WHERE code IN ('FIN001', 'FIN002', 'FIN003', 'OPS001', 'OPS002', 'OPS003')"))
