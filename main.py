import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
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

# Adicione este bloco no final do arquivo
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))