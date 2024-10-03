import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para usar sessões
db = SQLAlchemy(app)

# Adicione esta nova rota para servir arquivos estáticos
@app.route('/assets/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Aqui você implementará a lógica de autenticação
        # Por enquanto, vamos apenas simular um login bem-sucedido
        session['logged_in'] = True
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # Aqui você implementará a lógica de cadastro
        # Por enquanto, vamos apenas simular um cadastro bem-sucedido
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/')
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
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
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Adicione este bloco no final do arquivo
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))