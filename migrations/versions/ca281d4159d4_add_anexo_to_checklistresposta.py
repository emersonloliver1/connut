"""Add anexo to ChecklistResposta

Revision ID: ca281d4159d4
Revises: 39e971d8ea61
Create Date: 2023-06-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca281d4159d4'
down_revision = '39e971d8ea61'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table with the desired schema
    op.create_table('new_checklist_resposta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=False),
        sa.Column('questao_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.String(length=500), nullable=False),
        sa.Column('conformidade', sa.String(length=50), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('anexo', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Copy data from the old table to the new table
    op.execute('INSERT INTO new_checklist_resposta (id, checklist_id, questao_id, descricao, conformidade, observacoes) SELECT id, checklist_id, questao_id, descricao, conformidade, observacoes FROM checklist_resposta')

    # Drop the old table
    op.drop_table('checklist_resposta')

    # Rename the new table to the original name
    op.rename_table('new_checklist_resposta', 'checklist_resposta')


def downgrade():
    # Create the original table
    op.create_table('old_checklist_resposta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=False),
        sa.Column('questao_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.String(length=500), nullable=False),
        sa.Column('conformidade', sa.String(length=50), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Copy data back, excluding the 'anexo' column
    op.execute('INSERT INTO old_checklist_resposta (id, checklist_id, questao_id, descricao, conformidade, observacoes) SELECT id, checklist_id, questao_id, descricao, conformidade, observacoes FROM checklist_resposta')

    # Drop the new table
    op.drop_table('checklist_resposta')

    # Rename the old table back to the original name
    op.rename_table('old_checklist_resposta', 'checklist_resposta')
