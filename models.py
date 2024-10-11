from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    crn = db.Column(db.String(20))  # Certifique-se de que esta linha existe

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_pessoa = db.Column(db.String(10), nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('documentos', lazy=True))

class Checklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    avaliador = db.Column(db.String(100), nullable=False)
    data_inspecao = db.Column(db.Date, nullable=False)
    area_observada = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    porcentagem_conformidade = db.Column(db.Float, nullable=False)
    tipo_checklist = db.Column(db.String(50), nullable=False)
    crn = db.Column(db.String(20))  # Adicionando o campo CRN

    cliente = db.relationship('Cliente', backref=db.backref('checklists', lazy=True))

class ChecklistResposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=False)
    questao_id = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    conformidade = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.Text)
    anexo = db.Column(db.String(255))
    secao = db.Column(db.String(255))  # Novo campo para a seção da questão

    checklist = db.relationship('Checklist', backref=db.backref('respostas', lazy=True))

    def __repr__(self):
        return f'<ChecklistResposta {self.id}>'
