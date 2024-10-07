import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

app = Flask(__name__, static_folder='assets', static_url_path='/assets')

# Configuração do banco de dados SQLite local
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua_chave_secreta_aqui')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Por favor, tente novamente.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email já existe. Por favor, use outro email.')
        else:
            new_user = User(name=name, email=email, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
@login_required
def index():
    menu_items = [
        {"icon": "📊", "text": "Dashboard"},
        {"icon": "👥", "text": "Clientes"},
        {"icon": "📝", "text": "Planos de Ação"},
        {"icon": "📎", "text": "Documentos"},
        {"icon": "📋", "text": "Cardápios"},
        {"icon": "🌡️", "text": "Temperaturas"},
        {"icon": "📊", "text": "Relatórios"},
        {"icon": "✅", "text": "Checklists"},
        {"icon": "📊", "text": "Avaliações"},
        {"icon": "💬", "text": "Atendimentos"},
        {"icon": "📄", "text": "Laudos"},
        {"icon": "❓", "text": "Ajuda"}
    ]
    return render_template('index.html', menu_items=menu_items)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Aqui você pode adicionar lógica para buscar dados reais do banco de dados
    total_clientes = 100  # exemplo
    planos_ativos = 25  # exemplo
    documentos_pendentes = 10  # exemplo
    avaliacoes_realizadas = 50  # exemplo

    return render_template('dashboard.html',
                           total_clientes=total_clientes,
                           planos_ativos=planos_ativos,
                           documentos_pendentes=documentos_pendentes,
                           avaliacoes_realizadas=avaliacoes_realizadas)

@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'POST':
        novo_cliente = Cliente(
            nome=request.form['nome'],
            tipo_pessoa=request.form['tipoPessoa'],
            documento=request.form['documento'],
            telefone=request.form['telefone'],
            cep=request.form['cep'],
            endereco=request.form['endereco'],
            numero=request.form['numero'],
            complemento=request.form['complemento'],
            cidade=request.form['cidade'],
            estado=request.form['estado']
        )
        db.session.add(novo_cliente)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes'))
    
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/buscar_clientes')
@login_required
def buscar_clientes():
    termo = request.args.get('termo', '')
    clientes = Cliente.query.filter(Cliente.nome.ilike(f'%{termo}%')).all()
    return jsonify([{'id': c.id, 'nome': c.nome, 'documento': c.documento} for c in clientes])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Configuração para o Cloud Run
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)