from flask import Blueprint, render_template, request, flash, redirect, url_for
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
from models import User, db

def init_reset_password(app):
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
                flash('Funcionalidade temporariamente desabilitada.', 'info')
                return redirect(url_for('login'))
            else:
                flash('E-mail não encontrado', 'error')
        return render_template('reset_password_request.html')

    return reset_password_bp
