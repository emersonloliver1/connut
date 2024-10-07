import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from storage.storage import LocalJSONStorage
from flask_migrate import Migrate
from security.timestamp import init_session_timeout, check_session_timeout
from datetime import datetime

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configuração do banco de dados SQLite na pasta instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua_chave_secreta_aqui')

# Configuração para upload de arquivos
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

document_storage = LocalJSONStorage()

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

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('documentos', lazy=True))

migrate = Migrate(app, db)

init_session_timeout(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['last_activity'] = datetime.utcnow().isoformat()
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
@check_session_timeout
def index():
    menu_items = [
        {"icon": "📊", "text": "Dashboard", "url": url_for('dashboard')},
        {"icon": "👥", "text": "Clientes", "url": url_for('clientes')},
        {"icon": "📝", "text": "Planos de Ação", "url": "#"},
        {"icon": "📎", "text": "Documentos", "url": url_for('documentos')},
        {"icon": "📋", "text": "Cardápios", "url": "#"},
        {"icon": "🌡️", "text": "Temperaturas", "url": "#"},
        {"icon": "📊", "text": "Relatórios", "url": "#"},
        {"icon": "✅", "text": "Checklists", "url": url_for('checklists')},
        {"icon": "📊", "text": "Avaliações", "url": "#"},
        {"icon": "💬", "text": "Atendimentos", "url": "#"},
        {"icon": "📄", "text": "Laudos", "url": "#"},
        {"icon": "❓", "text": "Ajuda", "url": "#"}
    ]
    return render_template('index.html', menu_items=menu_items, current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@check_session_timeout
def dashboard():
    # Buscando dados reais do banco de dados
    total_clientes = Cliente.query.count()
    
    # Placeholder para dados que ainda não temos
    planos_ativos = 0  # Será implementado quando tivermos a classe PlanoAcao
    documentos_pendentes = 0  # Temporariamente definido como 0 até resolvermos o problema do banco de dados
    avaliacoes_realizadas = 0  # Será implementado quando tivermos a classe Avaliacao

    return render_template('dashboard.html',
                           total_clientes=total_clientes,
                           planos_ativos=planos_ativos,
                           documentos_pendentes=documentos_pendentes,
                           avaliacoes_realizadas=avaliacoes_realizadas,
                           current_user=current_user)

@app.route('/clientes', methods=['GET', 'POST'])
@login_required
@check_session_timeout
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
        return jsonify({'message': 'Cliente cadastrado com sucesso!'}), 201
    
    return render_template('clientes.html', current_user=current_user)

@app.route('/buscar_clientes')
@login_required
def buscar_clientes():
    termo = request.args.get('termo', '')
    clientes = Cliente.query.filter(Cliente.nome.ilike(f'%{termo}%')).all()
    return jsonify([{
        'id': c.id, 
        'nome': c.nome,
        'documento': c.documento,
        'telefone': c.telefone,
        'cep': c.cep,
        'endereco': c.endereco,
        'numero': c.numero,
        'complemento': c.complemento,
        'cidade': c.cidade,
        'estado': c.estado
    } for c in clientes])

@app.route('/buscar_cliente/<int:id>')
@login_required
def buscar_cliente(id):
    cliente = Cliente.query.get(id)
    if cliente:
        return jsonify({
            'id': cliente.id,
            'nome': cliente.nome,
            'telefone': cliente.telefone,
            'cep': cliente.cep,
            'endereco': cliente.endereco,
            'numero': cliente.numero,
            'complemento': cliente.complemento,
            'cidade': cliente.cidade,
            'estado': cliente.estado
        })
    return jsonify({'error': 'Cliente não encontrado'}), 404

@app.route('/atualizar_cliente', methods=['POST'])
@login_required
def atualizar_cliente():
    cliente_id = request.form.get('id')
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        cliente.nome = request.form.get('nome')
        cliente.telefone = request.form.get('telefone')
        cliente.cep = request.form.get('cep')
        cliente.endereco = request.form.get('endereco')
        cliente.numero = request.form.get('numero')
        cliente.complemento = request.form.get('complemento')
        cliente.cidade = request.form.get('cidade')
        cliente.estado = request.form.get('estado')
        db.session.commit()
        return jsonify({'message': 'Cliente atualizado com sucesso'}), 200
    return jsonify({'error': 'Cliente não encontrado'}), 404

@app.route('/excluir_cliente/<int:id>', methods=['DELETE'])
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({'message': 'Cliente excluído com sucesso'}), 200

# Rotas para documentos

@app.route('/documentos')
@login_required
@check_session_timeout
def documentos():
    return render_template('documentos.html', current_user=current_user)

@app.route('/buscar_documentos')
@login_required
def buscar_documentos():
    termo = request.args.get('termo', '')
    app.logger.info(f"Buscando documentos com termo: '{termo}'")
    try:
        documentos = Documento.query.join(Cliente).filter(
            (Documento.nome.ilike(f'%{termo}%')) | (Cliente.nome.ilike(f'%{termo}%'))
        ).all()
        app.logger.info(f"Documentos encontrados: {len(documentos)}")
        resultado = [{
            'id': doc.id,
            'name': doc.nome,
            'client': doc.cliente.nome
        } for doc in documentos]
        app.logger.info(f"Resultado da busca: {resultado}")
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Erro ao buscar documentos: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_documento', methods=['POST'])
@login_required
def upload_documento():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if 'cliente_id' not in request.form:
        return jsonify({'error': 'ID do cliente não fornecido'}), 400

    cliente_id = request.form['cliente_id']
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado'}), 404

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_content = file.read()
        
        novo_documento = Documento(
            nome=filename,
            tipo_arquivo=file.content_type,
            cliente_id=cliente_id
        )
        db.session.add(novo_documento)
        db.session.commit()
        
        document_storage.save(novo_documento.id, file_content)
        return jsonify({'message': 'Documento enviado com sucesso'}), 201
    
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

@app.route('/excluir_documento/<int:id>', methods=['DELETE'])
@login_required
def excluir_documento(id):
    documento = Documento.query.get_or_404(id)
    document_storage.delete(documento.id)
    db.session.delete(documento)
    db.session.commit()
    return jsonify({'message': 'Documento excluído com sucesso'}), 200

@app.route('/buscar_clientes_para_documentos')
@login_required
def buscar_clientes_para_documentos():
    clientes = Cliente.query.all()
    app.logger.info(f"Buscando clientes para documentos. Total encontrado: {len(clientes)}")
    resultado = [{'id': c.id, 'nome': c.nome} for c in clientes]
    app.logger.info(f"Resultado da busca de clientes: {resultado}")
    return jsonify(resultado)

@app.route('/buscar_documentos_por_cliente/<int:cliente_id>')
@login_required
def buscar_documentos_por_cliente(cliente_id):
    try:
        documentos = Documento.query.filter_by(cliente_id=cliente_id).all()
        app.logger.info(f"Documentos encontrados para o cliente {cliente_id}: {len(documentos)}")
        resultado = [{
            'id': doc.id,
            'nome': doc.nome,
            'tipo_arquivo': doc.tipo_arquivo
        } for doc in documentos]
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Erro ao buscar documentos do cliente {cliente_id}: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/checklists')
@login_required
@check_session_timeout
def checklists():
    app.logger.info("Rota /checklists foi acessada")
    return render_template('checklists.html', current_user=current_user)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)