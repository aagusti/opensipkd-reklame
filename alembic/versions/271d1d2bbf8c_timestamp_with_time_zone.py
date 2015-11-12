"""timestamp with time zone

Revision ID: 271d1d2bbf8c
Revises: 
Create Date: 2015-11-03 21:24:54.926719

"""

# revision identifiers, used by Alembic.
revision = '271d1d2bbf8c'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('users', 'last_login_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))
    op.alter_column('users', 'registered_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))
    op.alter_column('users', 'security_code_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))

def downgrade():
    pass
