import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from storage.storage import LocalJSONStorage
from flask_migrate import Migrate
from security.timestamp import init_session_timeout, check_session_timeout
from datetime import datetime
import io
import json
from sqlalchemy import Float
from models import db, User, Cliente, Documento, Checklist, ChecklistResposta
from weasyprint import HTML, CSS
from flask_cors import CORS

def remover_duplicatas(respostas):
    vistas = set()
    unicas = []
    for resposta in respostas:
        if resposta.descricao not in vistas:
            unicas.append(resposta)
            vistas.add(resposta.descricao)
    return unicas

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Habilita CORS para todas as rotas

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua_chave_secreta_aqui')

# Configuração para upload de arquivos
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicialize o db com o app
db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

document_storage = LocalJSONStorage()

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
        crn = request.form.get('crn')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email já existe. Por favor, use outro email.')
        else:
            new_user = User(name=name, email=email, password=generate_password_hash(password, method='sha256'), crn=crn)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
@login_required
@check_session_timeout
def index():
    print(f"Current user: {current_user.name}")  # Adicione esta linha
    menu_items = [
        {"icon": "📊", "text": "Dashboard", "url": url_for('dashboard')},
        {"icon": "👥", "text": "Clientes", "url": url_for('clientes')},
        {"icon": "📝", "text": "Planos de Ação", "url": "#"},
        {"icon": "📎", "text": "Documentos", "url": url_for('documentos')},
        {"icon": "📋", "text": "Cardápios", "url": "#"},
        {"icon": "🌡️", "text": "Temperaturas", "url": "#"},
        {"icon": "📊", "text": "Relatórios", "url": url_for('relatorios')},
        {"icon": "✅", "text": "Checklists", "url": url_for('checklists')},
        {"icon": "📊", "text": "Avaliações", "url": "#"},
        {"icon": "💬", "text": "Atendimentos", "url": "#"},
        {"icon": "📄", "text": "Laudos", "url": "#"},
        {"icon": "❓", "text": "Ajuda", "url": "#"},
        {"icon": "📦", "text": "Estoque", "url": url_for('estoque')}
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

# Certifique-se de que a pasta de uploads existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Inicialize o armazenamento local JSON
local_storage = LocalJSONStorage()

# ... (outras rotas existentes)

@app.route('/salvar-checklist', methods=['POST'])
@login_required
def salvar_checklist():
    app.logger.info("Rota /salvar-checklist acessada")
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
            tipo_checklist='higienico_sanitario'  # Adicionado o tipo de checklist
        )
        db.session.add(novo_checklist)
        db.session.flush()
        
        for index, resposta in enumerate(json_data['respostas']):
            anexo_key = f'anexo_{index}'
            anexo_path = None
            
            if anexo_key in request.files:
                file = request.files[anexo_key]
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    anexo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(anexo_path)
            
            nova_resposta = ChecklistResposta(
                checklist_id=novo_checklist.id,
                questao_id=resposta['id'],
                descricao=resposta['descricao'],
                conformidade=resposta['conformidade'],
                observacoes=resposta.get('observacoes', ''),
                anexo=anexo_path
            )
            db.session.add(nova_resposta)
        
        db.session.commit()
        app.logger.info(f"Checklist salvo com sucesso: ID={novo_checklist.id}")
        return jsonify({"message": "Checklist salvo com sucesso!", "id": novo_checklist.id}), 200
    except Exception as e:
        app.logger.error(f"Erro ao salvar checklist: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
        
        app.logger.info(f"Dados recebidos para salvar checklist RDC 216: {json_data}")
        
        novo_checklist = Checklist(
            cliente_id=json_data['clienteId'],
            avaliador=json_data['avaliador'],
            data_inspecao=datetime.strptime(json_data['dataInspecao'], '%Y-%m-%d').date(),
            area_observada=json_data['areaObservada'],
            status='concluido',
            porcentagem_conformidade=float(json_data['porcentagemConformidade']),
            tipo_checklist='rdc216'
        )
        db.session.add(novo_checklist)
        db.session.flush()
        
        # Adicione um log aqui para verificar se o checklist está sendo salvo corretamente
        app.logger.info(f"Novo checklist RDC 216 salvo: ID={novo_checklist.id}, Tipo={novo_checklist.tipo_checklist}")
        
        for resposta in json_data['respostas']:
            nova_resposta = ChecklistResposta(
                checklist_id=novo_checklist.id,
                questao_id=resposta['id'],
                descricao=resposta['descricao'],
                conformidade=resposta['conformidade'],
                observacoes=resposta['observacoes']
            )
            
            if resposta.get('anexo'):
                arquivo = request.files.get(f"anexo_{resposta['id']}")
                if arquivo:
                    filename = secure_filename(arquivo.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    arquivo.save(file_path)
                    nova_resposta.anexo = filename
            
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

@app.route('/relatorios', methods=['GET', 'POST'])
@login_required
@check_session_timeout
def relatorios():
    clientes = Cliente.query.all()
    
    if request.method == 'POST':
        cliente_id = request.form.get('cliente')
        cliente = Cliente.query.get(cliente_id)
        
        if cliente:
            checklists = Checklist.query.filter_by(cliente_id=cliente.id).all()
            
            return render_template('selecao_checklist.html', 
                                   cliente=cliente, 
                                   checklists=checklists)
        else:
            flash('Cliente não encontrado.', 'error')
    
    return render_template('relatorios.html', clientes=clientes)

@app.route('/gerar_relatorio/<int:cliente_id>/<int:checklist_id>')
@login_required
@check_session_timeout
def gerar_relatorio(cliente_id, checklist_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    checklist = Checklist.query.get_or_404(checklist_id)
    
    respostas = ChecklistResposta.query.filter_by(checklist_id=checklist.id).all()
    
    # Remover duplicatas
    respostas_unicas = remover_duplicatas(respostas)
    
    relatorio = {
        'cliente_id': cliente.id,
        'checklist_id': checklist.id,
        'nome_cliente': cliente.nome,
        'tipo_checklist': checklist.tipo_checklist,
        'data_inspecao': checklist.data_inspecao,
        'area_observada': checklist.area_observada,
        'avaliador': checklist.avaliador,
        'porcentagem_conformidade': checklist.porcentagem_conformidade,
        'respostas_unicas': respostas_unicas
    }
    
    return render_template('relatorio_detalhado.html', relatorio=relatorio)

@app.route('/exportar_pdf/<int:cliente_id>/<int:checklist_id>')
@login_required
@check_session_timeout
def exportar_pdf(cliente_id, checklist_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    checklist = Checklist.query.get_or_404(checklist_id)
    respostas = ChecklistResposta.query.filter_by(checklist_id=checklist.id).all()
    
    # Remover duplicatas
    respostas_unicas = []
    descricoes_vistas = set()
    for resposta in respostas:
        if resposta.descricao not in descricoes_vistas:
            respostas_unicas.append(resposta)
            descricoes_vistas.add(resposta.descricao)
    
    # Organize as respostas por seção
    respostas_por_secao = {}
    for resposta in respostas_unicas:
        secao = resposta.secao or "Sem Seção"
        if secao not in respostas_por_secao:
            respostas_por_secao[secao] = []
        
        # Use uma URL para o anexo em vez de um caminho de arquivo
        anexo_url = None
        if resposta.anexo:
            anexo_url = url_for('uploads', filename=os.path.basename(resposta.anexo), _external=True)
        
        respostas_por_secao[secao].append({
            "descricao": resposta.descricao,
            "conformidade": resposta.conformidade,
            "observacoes": resposta.observacoes,
            "anexo": anexo_url
        })
    
    relatorio = {
        'cliente_id': cliente.id,
        'checklist_id': checklist.id,
        'nome_cliente': cliente.nome,
        'tipo_checklist': checklist.tipo_checklist.upper(),
        'data_inspecao': checklist.data_inspecao,
        'area_observada': checklist.area_observada,
        'avaliador': checklist.avaliador,
        'crn': current_user.crn or "0",
        'porcentagem_conformidade': checklist.porcentagem_conformidade,
        'respostas_por_secao': respostas_por_secao
    }
    
    html_content = render_template('relatorio_pdf.html', relatorio=relatorio)
    
    css = CSS(string='''
        @page { size: A4; margin: 1cm }
        body { font-family: Arial, sans-serif; }
        img { max-width: 100%; height: auto; }
    ''')
    
    pdf = HTML(string=html_content, base_url=request.url_root).write_pdf(stylesheets=[css])
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    
    return response

@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def gerar_pdf_checklist(checklist_id):
    # ... (código existente)

    for resposta in checklist.respostas:
        # ... (código existente para adicionar a resposta)

        if resposta.anexo:
            try:
                img = Image(resposta.anexo, width=200, height=150)
                elements.append(img)
            except Exception as e:
                print(f"Erro ao adicionar imagem: {e}")

    # ... (resto do código para gerar o PDF)

@app.route('/estoque')
@login_required
@check_session_timeout
def estoque():
    return render_template('estoque.html', current_user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados se não existirem
    
    # Configuração para o Google Cloud Run
    if os.environ.get('GOOGLE_CLOUD_RUN', 'False') == 'True':
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port)
    else:
        # Configuração para desenvolvimento local
        app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=True)