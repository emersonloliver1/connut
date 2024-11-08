"""Initial migration

Revision ID: 7996d3e3e525
Revises: 
Create Date: 2024-10-10 14:12:15.541258

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7996d3e3e525'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cliente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('tipo_pessoa', sa.String(length=10), nullable=False),
    sa.Column('documento', sa.String(length=20), nullable=False),
    sa.Column('telefone', sa.String(length=20), nullable=True),
    sa.Column('cep', sa.String(length=10), nullable=True),
    sa.Column('endereco', sa.String(length=200), nullable=True),
    sa.Column('numero', sa.String(length=10), nullable=True),
    sa.Column('complemento', sa.String(length=100), nullable=True),
    sa.Column('cidade', sa.String(length=100), nullable=True),
    sa.Column('estado', sa.String(length=2), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('documento')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('crn', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('avaliador', sa.String(length=100), nullable=False),
    sa.Column('data_inspecao', sa.Date(), nullable=False),
    sa.Column('area_observada', sa.String(length=200), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('porcentagem_conformidade', sa.Float(), nullable=False),
    sa.Column('tipo_checklist', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('documento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('tipo_arquivo', sa.String(length=50), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('checklist_resposta',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('checklist_id', sa.Integer(), nullable=False),
    sa.Column('questao_id', sa.String(length=50), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=False),
    sa.Column('conformidade', sa.Integer(), nullable=False),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('anexo', sa.String(length=255), nullable=True),
    sa.Column('secao', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('checklist_resposta')
    op.drop_table('documento')
    op.drop_table('checklist')
    op.drop_table('user')
    op.drop_table('cliente')
    # ### end Alembic commands ###
