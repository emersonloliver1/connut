from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

# Criação de um Blueprint para o módulo de Coleta de Amostras
coleta_amostras_bp = Blueprint('coleta_amostras', __name__, template_folder='templates')

UPLOAD_FOLDER = 'static/coleta_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@coleta_amostras_bp.route('/coleta-amostras')
def coleta_amostras():
    return render_template('coleta-amostras.html')

@coleta_amostras_bp.route('/submit-registros', methods=['POST'])
def submit_registros():
    items = request.form.getlist('item[]')
    anexos = request.files.getlist('anexo[]')
    datas_coleta = request.form.getlist('data_coleta[]')

    for item, anexo, data_coleta in zip(items, anexos, datas_coleta):
        if anexo and allowed_file(anexo.filename):
            filename = secure_filename(anexo.filename)
            anexo.save(os.path.join(UPLOAD_FOLDER, filename))
            # Aqui você pode adicionar a lógica para salvar os dados no banco de dados
            # Exemplo: salvar item, filename, data_coleta no banco de dados

    flash('Registros enviados com sucesso!', 'success')
    return redirect(url_for('coleta_amostras.coleta_amostras'))
