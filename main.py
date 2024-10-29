import sys
import os
# Adicione o diretório atual ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, make_response, send_from_directory, abort, current_app, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from storage.storage import LocalJSONStorage
from flask_migrate import Migrate, upgrade
from security.timestamp import init_session_timeout, check_session_timeout
from datetime import datetime
import io
import json
from sqlalchemy import Float
from models import db, User, Cliente, Documento, Checklist, ChecklistResposta
from weasyprint import HTML, CSS
from flask_cors import CORS
import traceback
from sqlalchemy.exc import IntegrityError
from functools import wraps
from datetime import datetime, timedelta
import threading
from coleta_amostras import coleta_amostras_bp
from database_config import DATABASE_URL, ssl_args
from reset_password import init_reset_password
from flask_mail import Mail
import requests

# No início do arquivo, após as importações
load_dotenv()  # Isso deve estar no início do arquivo, após as importações
# Configuração do logging
# Configuração do logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurações de cache
CACHE = {}
CACHE_TIMEOUT = timedelta(minutes=30)  # Ajuste conforme necessário

def limpar_cache():
    global CACHE
    agora = datetime.now()
    CACHE = {k: v for k, v in CACHE.items() if v['expira'] > agora}

def cache_com_timeout(timeout=CACHE_TIMEOUT):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f.__name__ + str(args) + str(kwargs)
            if cache_key in CACHE:
                if CACHE[cache_key]['expira'] > datetime.now():
                    return CACHE[cache_key]['valor']
            
            resultado = f(*args, **kwargs)
            CACHE[cache_key] = {
                'valor': resultado,
                'expira': datetime.now() + timeout
            }
            return resultado
        return decorated_function
    return decorator

def iniciar_limpeza_automatica(intervalo=300):  # 300 segundos = 5 minutos
    def limpeza_periodica():
        while True:
            limpar_cache()
            threading.Timer(intervalo, limpeza_periodica).start()
    
    threading.Timer(intervalo, limpeza_periodica).start()

def remover_duplicatas(respostas):
    vistas = {}
    for resposta in respostas:
        chave = resposta.descricao.strip().lower()
        if chave not in vistas or resposta.conformidade:
            vistas[chave] = resposta
    return list(vistas.values())

# Configurações de cache
CACHE = {}
CACHE_TIMEOUT = timedelta(minutes=30)  # Ajuste conforme necessário

def limpar_cache():
    global CACHE
    agora = datetime.now()
    CACHE = {k: v for k, v in CACHE.items() if v['expira'] > agora}

def cache_com_timeout(timeout=CACHE_TIMEOUT):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f.__name__ + str(args) + str(kwargs)
            if cache_key in CACHE:
                if CACHE[cache_key]['expira'] > datetime.now():
                    return CACHE[cache_key]['valor']
            
            resultado = f(*args, **kwargs)
            CACHE[cache_key] = {
                'valor': resultado,
                'expira': datetime.now() + timeout
            }
            return resultado
        return decorated_function
    return decorator

def iniciar_limpeza_automatica(intervalo=300):  # 300 segundos = 5 minutos
    def limpeza_periodica():
        while True:
            limpar_cache()
            threading.Timer(intervalo, limpeza_periodica).start()
    
    threading.Timer(intervalo, limpeza_periodica).start()

def remover_duplicatas(respostas):
    vistas = {}
    for resposta in respostas:
        chave = resposta.descricao.strip().lower()
        if chave not in vistas or resposta.conformidade:
            vistas[chave] = resposta
    return list(vistas.values())

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'emersonfilho953@gmail.com'
app.config['MAIL_PASSWORD'] = 'xsvw qxib kjyo tkdg'
app.config['MAIL_DEFAULT_SENDER'] = 'emersonfilho953@gmail.com'

mail = Mail(app)

# Inicialize o db com o app
db.init_app(app)

# Configuração para upload de arquivos
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}

migrate = Migrate(app, db)

def setup_database():
    logger.info("Iniciando setup do banco de dados...")
    try:
        with app.app_context():
            db.create_all()
        logger.info("Banco de dados configurado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao configurar o banco de dados: {str(e)}")
        raise

def apply_migrations():
    with app.app_context():
        upgrade()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

document_storage = LocalJSONStorage()

init_session_timeout(app)

# Adicione esta linha para debug
print(f"Bucket configurado: {bucket.name}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if user.password.startswith('pbkdf2:sha256:'):
                # Senha já está no formato correto
                if check_password_hash(user.password, password):
                    login_user(user)
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('index'))
            else:
                # Senha está em formato antigo, vamos verificar e atualizar
                if user.password == password:  # Assumindo que a senha antiga era armazenada em texto simples
                    # Atualizar para o novo formato de hash
                    user.password = generate_password_hash(password, method='pbkdf2:sha256')
                    db.session.commit()
                    login_user(user)
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('index'))
            flash('Senha incorreta. Por favor, tente novamente.')
        else:
            flash('Email não encontrado. Por favor, tente novamente.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        crn = request.form.get('crn')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(name=name, email=email, password=hashed_password, crn=crn)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro bem-sucedido! Por favor, faça login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
def landing():
    return render_template('landingpg.html')

# Mova a rota existente do index para um novo caminho
@app.route('/dashboard')
@login_required
@check_session_timeout
def index():
    try:
        logger.debug(f"Current user: {current_user.name}")
        menu_items = [
            {"icon": "📊", "text": "Dashboard", "url": url_for('dashboard')},
            {"icon": "👥", "text": "Clientes", "url": url_for('clientes')},
            {"icon": "📝", "text": "Planos de Ação", "url": "#"},
            {"icon": "📎", "text": "Documentos", "url": url_for('documentos')},
            {"icon": "📋", "text": "Cardápios", "url": "#"},
            {"icon": "🌡️", "text": "Temperaturas", "url": "#"},
            {"icon": "📊", "text": "Relatórios", "url": url_for('relatorios')},  # Usando a nova rota
            {"icon": "✅", "text": "Checklists", "url": url_for('checklists')},
            {"icon": "📊", "text": "Avaliações", "url": "#"},
            {"icon": "💬", "text": "Atendimentos", "url": "#"},
            {"icon": "📄", "text": "Laudos", "url": "#"},
            {"icon": "❓", "text": "Ajuda", "url": "#"},
            {"icon": "📦", "text": "Estoque", "url": url_for('estoque')},
            {"icon": "🧪", "text": "Coleta de Amostras", "url": url_for('coleta_amostras.coleta_amostras')}
        ]
        return render_template('index.html', menu_items=menu_items, current_user=current_user)
    except Exception as e:
        logger.error(f"Erro na rota index: {str(e)}")
        return "Ocorreu um erro interno", 500

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
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

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
        
        document_storage.save(str(novo_documento.id), file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content)
        return jsonify({'message': 'Documento enviado com sucesso'}), 201
    
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

@app.route('/excluir_documento/<int:id>', methods=['DELETE'])
@login_required
def excluir_documento(id):
    try:
        documento = Documento.query.get_or_404(id)
        app.logger.info(f"Tentando excluir documento com ID: {id}")
        
        # Tente excluir o documento do armazenamento
        try:
            document_storage.delete(str(documento.id))
            app.logger.info(f"Documento {id} excluído do armazenamento")
        except Exception as storage_error:
            app.logger.error(f"Erro ao excluir documento {id} do armazenamento: {str(storage_error)}")
            # Continua mesmo se falhar a exclusão do armazenamento
        
        # Exclui o documento do banco de dados
        db.session.delete(documento)
        db.session.commit()
        app.logger.info(f"Documento {id} excluído do banco de dados")
        
        return jsonify({'message': 'Documento excluído com sucesso'}), 200
    except Exception as e:
        app.logger.error(f"Erro ao excluir documento {id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir documento: {str(e)}'}), 500

@app.route('/buscar_clientes_para_documentos')
@login_required
def buscar_clientes_para_documentos():
    clientes = Cliente.query.all()
    return jsonify([{'id': c.id, 'nome': c.nome} for c in clientes])

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

@app.route('/visualizar_documento/<int:id>')
@login_required
def visualizar_documento(id):
    documento = Documento.query.get_or_404(id)
    conteudo = document_storage.load(str(documento.id))  # Convertemos para string
    if conteudo is None:
        return jsonify({'error': 'Documento não encontrado'}), 404
    return send_file(
        io.BytesIO(conteudo.encode('utf-8') if isinstance(conteudo, str) else conteudo),
        mimetype=documento.tipo_arquivo,
        as_attachment=True,
        download_name=documento.nome
    )

# Inicialize o armazenamento local JSON
local_storage = LocalJSONStorage()

# ... (outras rotas existentes)

@app.route('/salvar-checklist', methods=['POST'])
@login_required
def salvar_checklist():
    try:
        data = request.form
        json_data = json.loads(data.get('dados'))
        
        novo_checklist = Checklist(
            cliente_id=json_data['clienteId'],
            avaliador=json_data['avaliador'],
            data_inspecao=datetime.strptime(json_data['dataInspecao'], '%Y-%m-%d').date(),
            area_observada=json_data['areaObservada'],
            status='concluido',
            porcentagem_conformidade=float(json_data['porcentagemConformidade']),
            tipo_checklist='higienico-sanitario',
            crn=json_data.get('crn', '')
        )
        db.session.add(novo_checklist)
        db.session.flush()
        
        for resposta in json_data['respostas']:
            nova_resposta = ChecklistResposta(
                checklist_id=novo_checklist.id,
                questao_id=resposta['id'],
                descricao=resposta['descricao'],
                conformidade=resposta['conformidade'],
                observacoes=resposta['observacoes']
            )
            
            # Processa o anexo, se houver
            if f"anexo_{resposta['id']}" in request.files:
                arquivo = request.files[f"anexo_{resposta['id']}"]
                if arquivo and arquivo.filename != '':
                    filename = f"{novo_checklist.id}_{resposta['id']}_{secure_filename(arquivo.filename)}"
                    blob = bucket.blob(filename)
                    blob.upload_from_string(
                        arquivo.read(),
                        content_type=arquivo.content_type
                    )
                    nova_resposta.anexo = filename
                    print(f"Anexo salvo no GCS: {filename}")  # Log para debug
            
            db.session.add(nova_resposta)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Checklist salvo com sucesso!'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao salvar checklist: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Remova ou comente a função salvar_checklist duplicada

@app.route('/salvar-progresso-checklist', methods=['POST'])
@login_required
def salvar_progresso_checklist():
    data = request.json
    
    # Verificar se já existe um checklist em progresso para este cliente
    checklist_existente = Checklist.query.filter_by(
        cliente_id=data['clienteId'],
        status='em_progresso'
    ).first()

    if checklist_existente:
        # Atualizar o checklist existente
        checklist = checklist_existente
    else:
        # Criar novo checklist
        checklist = Checklist(
            cliente_id=data['clienteId'],
            avaliador=data['avaliador'],
            data_inspecao=datetime.strptime(data['dataInspecao'], '%Y-%m-%d').date(),
            area_observada=data['areaObservada'],
            status='em_progresso'
        )
        db.session.add(checklist)

    # Atualizar ou criar respostas
    for resposta_data in data['respostas']:
        resposta = ChecklistResposta.query.filter_by(
            checklist_id=checklist.id,
            questao_id=resposta_data['id']
        ).first()

        if resposta:
            # Atualizar resposta existente
            resposta.conformidade = resposta_data['conformidade']
            resposta.observacoes = resposta_data['observacoes']
        else:
            # Criar nova resposta
            nova_resposta = ChecklistResposta(
                checklist_id=checklist.id,
                questao_id=resposta_data['id'],
                descricao=resposta_data['descricao'],
                conformidade=resposta_data['conformidade'],
                observacoes=resposta_data['observacoes']
            )
            db.session.add(nova_resposta)

    db.session.commit()
    return jsonify({'message': 'Progresso do checklist salvo com sucesso!', 'id': checklist.id}), 200

@app.route('/salvar-checklist-rdc216', methods=['POST'])
@login_required
def salvar_checklist_rdc216():
    try:
        data = request.form
        json_data = json.loads(data.get('dados'))
        
        novo_checklist = Checklist(
            cliente_id=json_data['clienteId'],
            avaliador=json_data['avaliador'],
            data_inspecao=datetime.strptime(json_data['dataInspecao'], '%Y-%m-%d').date(),
            area_observada=json_data['areaObservada'],
            status='concluido',
            porcentagem_conformidade=float(json_data['porcentagemConformidade']),
            tipo_checklist='rdc216',
            crn=json_data.get('crn', '')
        )
        db.session.add(novo_checklist)
        db.session.flush()
        
        for resposta in json_data['respostas']:
            nova_resposta = ChecklistResposta(
                checklist_id=novo_checklist.id,
                questao_id=resposta['id'],
                descricao=resposta['descricao'],
                conformidade=resposta['conformidade'],
                observacoes=resposta['observacoes']
            )
            
            # Processa o anexo, se houver
            if f"anexo_{resposta['id']}" in request.files:
                arquivo = request.files[f"anexo_{resposta['id']}"]
                if arquivo and arquivo.filename != '':
                    filename = f"{novo_checklist.id}_{resposta['id']}_{secure_filename(arquivo.filename)}"
                    blob = bucket.blob(filename)
                    blob.upload_from_string(
                        arquivo.read(),
                        content_type=arquivo.content_type
                    )
                    nova_resposta.anexo = filename
                    print(f"Anexo salvo no GCS: {filename}")  # Log para debug
            
            db.session.add(nova_resposta)
        
        db.session.commit()
        
        app.logger.info(f"Checklist RDC 216 salvo com sucesso: ID={novo_checklist.id}")
        
        return jsonify({
            'message': 'Checklist RDC 216 salvo com sucesso!',
            'id': novo_checklist.id,
            'porcentagem_conformidade': novo_checklist.porcentagem_conformidade
        }), 200
    except Exception as e:
        app.logger.error(f"Erro ao salvar checklist RDC 216: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Erro ao salvar checklist: {str(e)}'}), 500

@app.route('/check-db')
def check_db():
    try:
        # Tente fazer uma consulta simples
        checklist_count = Checklist.query.count()
        return jsonify({
            'status': 'OK',
            'message': f'Conexão com o banco de dados estabelecida. Total de checklists: {checklist_count}'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'Error',
            'message': f'Erro ao conectar com o banco de dados: {str(e)}'
        }), 500

<<<<<<< HEAD
=======
@app.route('/relatorios')
@login_required
@check_session_timeout
def relatorios():
    cliente_id = request.args.get('cliente', type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    query = Checklist.query

    if cliente_id:
        query = query.filter(Checklist.cliente_id == cliente_id)
    if data_inicio:
        query = query.filter(Checklist.data_inspecao >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Checklist.data_inspecao <= datetime.strptime(data_fim, '%Y-%m-%d').date())

    relatorios = query.order_by(Checklist.data_inspecao.desc()).all()
    clientes = Cliente.query.all()

    return render_template('relatorios.html', relatorios=relatorios, clientes=clientes)

import base64

@app.route('/exportar_pdf/<int:cliente_id>/<int:checklist_id>')
@login_required
@check_session_timeout
@cache_com_timeout(timedelta(minutes=5))
def exportar_pdf(cliente_id, checklist_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    checklist = Checklist.query.get_or_404(checklist_id)
    
    respostas = ChecklistResposta.query.filter_by(checklist_id=checklist.id).all()
    respostas_unicas = remover_duplicatas(respostas)
    
    respostas_organizadas = []
    for resposta in respostas_unicas:
        if resposta.conformidade and resposta.conformidade != '':
            anexo_data = None
            if resposta.anexo:
                anexo_path = os.path.join(app.config['UPLOAD_FOLDER'], resposta.anexo)
                if os.path.exists(anexo_path):
                    with open(anexo_path, "rb") as image_file:
                        anexo_data = base64.b64encode(image_file.read()).decode('utf-8')
                    print(f"Anexo encontrado: {anexo_path}")  # Log para debug
                else:
                    print(f"Arquivo não encontrado: {anexo_path}")  # Log para debug
            
            respostas_organizadas.append({
                "descricao": resposta.descricao,
                "conformidade": resposta.conformidade,
                "observacoes": resposta.observacoes,
                "anexo": anexo_data
            })

    print(f"Total de respostas organizadas: {len(respostas_organizadas)}")

    relatorio = {
        "nome_cliente": cliente.nome,
        "tipo_checklist": checklist.tipo_checklist,
        "data_inspecao": checklist.data_inspecao,
        "area_observada": checklist.area_observada,
        "avaliador": checklist.avaliador,
        "crn": checklist.crn,
        "porcentagem_conformidade": checklist.porcentagem_conformidade,
        "respostas": respostas_organizadas
    }

    rendered = render_template('relatorio_pdf.html', relatorio=relatorio)
    
    # Usando WeasyPrint para gerar o PDF
    html = HTML(string=rendered)
    pdf = html.write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=relatorio_{cliente.nome}_{checklist.data_inspecao}.pdf'

    return response

# Adicione esta rota para servir os arquivos de upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#tamanho máximo upload
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

>>>>>>> 03f9f2cd84f4351cb2edb316bc5bd77aacb95787
@app.route('/estoque')
@login_required
@check_session_timeout
def estoque():
    return render_template('estoque.html', current_user=current_user)

@app.route('/excluir_relatorio/<int:id>', methods=['POST'])
@login_required
def excluir_relatorio(id):
    try:
        checklist = Checklist.query.get_or_404(id)
        
        # Remova esta verificação se não for necessária
        # if checklist.usuario_id != current_user.id:
        #     return jsonify({'success': False, 'message': 'Você não tem permissão para excluir este relatório'}), 403
        
        # Primeiro, exclua todas as respostas associadas a este checklist
        ChecklistResposta.query.filter_by(checklist_id=id).delete()
        
        # Agora, exclua o checklist
        db.session.delete(checklist)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Relatório excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        error_message = f"Erro ao excluir relatório: {str(e)}\n{traceback.format_exc()}"
        app.logger.error(error_message)
        return jsonify({'success': False, 'message': error_message}), 500

@app.route('/inspecionar_dados/<int:checklist_id>')
@login_required
def inspecionar_dados(checklist_id):
    respostas = ChecklistResposta.query.filter_by(checklist_id=checklist_id).all()
    dados = [{
        'id': r.id,
        'descricao': r.descricao,
        'questao_id': r.questao_id,
        'conformidade': r.conformidade
    } for r in respostas]
    return jsonify(dados)

def limpar_cache():
    global CACHE
    agora = datetime.now()
    CACHE = {k: v for k, v in CACHE.items() if v['expira'] > agora}

def cache_com_timeout(timeout=CACHE_TIMEOUT):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f.__name__ + str(args) + str(kwargs)
            if cache_key in CACHE:
                if CACHE[cache_key]['expira'] > datetime.now():
                    return CACHE[cache_key]['valor']
            
            resultado = f(*args, **kwargs)
            CACHE[cache_key] = {
                'valor': resultado,
                'expira': datetime.now() + timeout
            }
            return resultado
        return decorated_function
    return decorator

def iniciar_limpeza_automatica(intervalo=300):  # 300 segundos = 5 minutos
    def limpeza_periodica():
        while True:
            limpar_cache()
            threading.Timer(intervalo, limpeza_periodica).start()
    
    threading.Timer(intervalo, limpeza_periodica).start()

app.register_blueprint(coleta_amostras_bp)

@app.route('/upload_anexo', methods=['POST'])
@login_required
def upload_anexo():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    secao_index = request.form.get('secao_index')
    item_index = request.form.get('item_index')
    checklist_type = request.form.get('checklist_type')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        blob = bucket.blob(filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )
        
        return jsonify({'success': True, 'message': 'Anexo enviado com sucesso', 'filename': filename}), 200
    
    return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400

@app.route('/update_all_passwords', methods=['GET'])
def update_all_passwords():
    users = User.query.all()
    for user in users:
        if not user.password.startswith('pbkdf2:sha256:'):
            # Assumindo que a senha antiga era armazenada em texto simples
            user.password = generate_password_hash(user.password, method='pbkdf2:sha256')
    db.session.commit()
    return 'Todas as senhas foram atualizadas para o novo formato.'

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')

def send_email(to_email, subject, content):
    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={"from": f"CONNUT <mailgun@{MAILGUN_DOMAIN}>",
              "to": [to_email],
              "subject": subject,
              "html": content})

# Modifique a função reset_password_request para usar send_email

reset_password_bp = init_reset_password(app, send_email)
app.register_blueprint(reset_password_bp)

def generate_signed_url(blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket('connut_storage_bucket')
    blob = bucket.blob(blob_name)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="GET",
    )
    
    return url

@app.route('/gerar-relatorio/<int:cliente_id>/<int:checklist_id>')
@login_required
def gerar_relatorio(cliente_id, checklist_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    checklist = Checklist.query.get_or_404(checklist_id)
    
    respostas = ChecklistResposta.query.filter_by(checklist_id=checklist.id).all()
    
    relatorio = {
        'nome_cliente': cliente.nome,
        'data_inspecao': checklist.data_inspecao,
        'area_observada': checklist.area_observada,
        'avaliador': checklist.avaliador,
        'porcentagem_conformidade': checklist.porcentagem_conformidade,
        'respostas': []
    }
    
    for resposta in respostas:
        print(f"Anexo original: {resposta.anexo}")  # Log para debug
        item = {
            'descricao': resposta.descricao,
            'conformidade': resposta.conformidade,
            'observacoes': resposta.observacoes,
            'anexo': generate_signed_url(resposta.anexo) if resposta.anexo else None
        }
        print(f"URL assinada: {item['anexo']}")  # Log para debug
        relatorio['respostas'].append(item)
    
    html = render_template('relatorio_pdf.html', relatorio=relatorio)
    
    # Configurar opções do WeasyPrint
    css = CSS(string='''
        @page { size: A4; margin: 1cm; }
        body { font-family: Arial, sans-serif; }
        img { max-width: 100%; height: auto; }
    ''')
    
    pdf = HTML(string=html).write_pdf(stylesheets=[css])
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=relatorio_{cliente.nome}_{checklist.data_inspecao}.pdf'
    
    return response

print(f"MAILGUN_DOMAIN: {os.getenv('MAILGUN_DOMAIN')}")
print(f"MAILGUN_API_KEY: {os.getenv('MAILGUN_API_KEY')}")

@app.route('/relatorios')
@login_required
@check_session_timeout
def relatorios():
    message = """
    {% extends "base.html" %}
    {% block content %}
    <h2>Relatórios</h2>
    <p>Esta funcionalidade está em desenvolvimento e estará disponível em breve.</p>
    {% endblock %}
    """
    return render_template_string(message)

if __name__ == '__main__':
    iniciar_limpeza_automatica()

if __name__ == '__main__':
    try:
        logger.info("Iniciando o aplicativo...")
        with app.app_context():
            setup_database()
        logger.info("Configuração do banco de dados concluída.")
        
        port = int(os.getenv('PORT', 8080))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Erro ao iniciar o aplicativo: {str(e)}")
        logger.error(traceback.format_exc())
<<<<<<< HEAD

=======
>>>>>>> 03f9f2cd84f4351cb2edb316bc5bd77aacb95787
