from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from weasyprint import HTML
from io import BytesIO
import base64

# Criação de um Blueprint para o módulo de Coleta de Amostras
coleta_amostras_bp = Blueprint('coleta_amostras', __name__, template_folder='templates')

UPLOAD_FOLDER = 'static/coleta_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Lista para armazenar registros (substitua por banco de dados em produção)
registros = []

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
            registro_id = len(registros) + 1
            registros.append({
                'id': registro_id,
                'item': item,
                'filename': filename,
                'data_coleta': data_coleta,
                'nutricionista': request.form['nutricionista'],
                'crn': request.form['crn'],
                'tipo_refeicao': {
                    'cafe': 'Café da Manhã',
                    'almoco': 'Almoço',
                    'jantar': 'Jantar'
                }.get(request.form['tipoRefeicao'], ''),
                'observacoes': request.form['observacoes']
            })

            # Gerar PDF
            registro = registros[-1]
            image_path = os.path.join(UPLOAD_FOLDER, registro['filename'])
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

            logo_path = 'static/logo.jpg'
            html = render_template('pdf_template.html', registro=registro, encoded_image=encoded_image, logo_path=logo_path)
            pdf = HTML(string=html).write_pdf()
            pdf_path = os.path.join(UPLOAD_FOLDER, f'registro_{registro_id}.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(pdf)

    flash('Registros enviados e PDFs gerados com sucesso!', 'success')
    return redirect(url_for('coleta_amostras.consultar_registros'))

@coleta_amostras_bp.route('/consultar-registros')
def consultar_registros():
    return render_template('consultar-registros.html', registros=registros)

@coleta_amostras_bp.route('/gerar-pdf/<int:registro_id>')
def gerar_pdf(registro_id):
    registro = next((r for r in registros if r['id'] == registro_id), None)
    if not registro:
        flash('Registro não encontrado!', 'error')
        return redirect(url_for('coleta_amostras.consultar_registros'))

    # Carregar imagem como base64
    image_path = os.path.join(UPLOAD_FOLDER, registro['filename'])
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    logo_path = 'static/logo.jpg'
    html = render_template('pdf_template.html', registro=registro, encoded_image=encoded_image, logo_path=logo_path)
    pdf = HTML(string=html).write_pdf()
    return send_file(BytesIO(pdf), as_attachment=True, download_name=f'registro_{registro_id}.pdf', mimetype='application/pdf')
