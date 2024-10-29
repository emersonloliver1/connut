from flask import Blueprint, render_template, request, flash, redirect, url_for
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
from models import User, db

def init_reset_password(app, send_email_func):
    reset_password_bp = Blueprint('reset_password', __name__)

    def generate_token(email):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='password-reset-salt')

    @reset_password_bp.route('/reset_password_request', methods=['GET', 'POST'])
    def reset_password_request():
        if request.method == 'POST':
            email = request.form['email']
            user = User.query.filter_by(email=email).first()
            if user:
                token = generate_token(user.email)
                reset_url = url_for('reset_password.reset_password', token=token, _external=True)
                subject = 'Solicitação de Redefinição de Senha'
                content = f'Para redefinir sua senha, visite o seguinte link: {reset_url}'
                send_email_func(user.email, subject, content)
                flash('Um e-mail com instruções para redefinir sua senha foi enviado.', 'info')
                return redirect(url_for('login'))
            else:
                flash('E-mail não encontrado', 'error')
        return render_template('reset_password_request.html')

    @reset_password_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        try:
            serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
        except:
            flash('O link de redefinição de senha é inválido ou expirou.', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            user = User.query.filter_by(email=email).first()
            if user:
                new_password = request.form['password']
                user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                flash('Sua senha foi redefinida com sucesso.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Usuário não encontrado', 'error')
        
        return render_template('reset_password.html')

    return reset_password_bp
