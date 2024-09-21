"""create chatbot table

Revision ID: 94e67559313c
Revises: 
Create Date: 2024-09-21 16:41:10.739807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '94e67559313c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create Enum types
    modelengine = sa.Enum('OPENAI', 'ANTHROPIC', name='modelengine')
    datatype = sa.Enum('SQL', name='datatype')

    # Create the table
    op.create_table('chatbot',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('system_prompt', sa.Text, nullable=False),
        sa.Column('model', modelengine, nullable=False),
        sa.Column('data_source', datatype, nullable=False),
        sa.Column('url', sa.String(length=127), nullable=True),
        sa.Column('tables', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('chatbot')
    op.execute('DROP TYPE if exists modelengine')
    op.execute('DROP TYPE if exists datatype')
