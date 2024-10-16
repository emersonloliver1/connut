from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    crn = Column(String(20))

class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    tipo_pessoa = Column(String(10), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    telefone = Column(String(20))
    cep = Column(String(10))
    endereco = Column(String(200))
    numero = Column(String(10))
    complemento = Column(String(100))
    cidade = Column(String(100))
    estado = Column(String(2))

class Documento(db.Model):
    __tablename__ = 'documentos'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    tipo_arquivo = Column(String(50), nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    cliente = relationship('Cliente', backref='documentos')

class Checklist(db.Model):
    __tablename__ = 'checklists'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    avaliador = Column(String(100), nullable=False)
    data_inspecao = Column(Date, nullable=False)
    area_observada = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False)
    porcentagem_conformidade = Column(Float, nullable=False)
    tipo_checklist = Column(String(50), nullable=False)
    crn = Column(String(20))

    cliente = relationship('Cliente', backref='checklists')

class ChecklistResposta(db.Model):
    __tablename__ = 'checklist_respostas'

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id'), nullable=False)
    questao_id = Column(Integer, nullable=False)
    descricao = Column(String(500), nullable=False)
    conformidade = Column(String(50))
    observacoes = Column(Text)
    anexo = Column(String(255))

    __table_args__ = (UniqueConstraint('checklist_id', 'questao_id', name='uq_checklist_questao'),)

    checklist = relationship('Checklist', backref='respostas')

    def __repr__(self):
        return f'<ChecklistResposta {self.id}>'
