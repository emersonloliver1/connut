from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import User
from database_config import db
from supabase_config import supabase
import os
from werkzeug.security import generate_password_hash

def init_reset_password(app):
    reset_password_bp = Blueprint('reset_password', __name__)

    @reset_password_bp.route('/reset_password_request', methods=['GET', 'POST'])
    def reset_password_request():
        if request.method == 'POST':
            email = request.form['email']
            user = User.query.filter_by(email=email).first()
            
            if user:
                try:
                    # Configurar a URL de redirecionamento
                    redirect_url = request.host_url.rstrip('/') + url_for('reset_password.reset_password')
                    app.logger.info(f"Redirect URL: {redirect_url}")
                    
                    # Usar Supabase para enviar o email de redefinição
                    result = supabase.auth.reset_password_email(
                        email,
                        options={
                            "redirect_to": redirect_url
                        }
                    )
                    app.logger.info(f"Supabase response: {result}")
                    flash('Um email com instruções para redefinir sua senha foi enviado.', 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    app.logger.error(f"Detailed error: {str(e)}")
                    app.logger.exception("Stack trace:")
                    flash('Erro ao enviar email de redefinição.', 'error')
            else:
                flash('Email não encontrado.', 'error')
                
        return render_template('reset_password_request.html')

    @reset_password_bp.route('/reset_password', methods=['GET', 'POST'])
    def reset_password():
        token = request.args.get('token')
        
        if not token:
            flash('Token inválido ou expirado.', 'error')
            return redirect(url_for('login'))

        if request.method == 'POST':
            try:
                new_password = request.form['password']
                confirm_password = request.form['password_confirm']

                if new_password != confirm_password:
                    flash('As senhas não coincidem.', 'error')
                    return render_template('reset_password.html')

                # Verificar e atualizar a senha usando Supabase
                result = supabase.auth.verify_and_change_password(token, new_password)
                
                # Atualizar a senha no banco de dados local também
                email = result.user.email
                user = User.query.filter_by(email=email).first()
                if user:
                    user.password = generate_password_hash(new_password)
                    db.session.commit()
                
                flash('Sua senha foi atualizada com sucesso!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                app.logger.error(f"Erro ao redefinir senha: {str(e)}")
                flash('Ocorreu um erro ao redefinir sua senha.', 'error')
                
        return render_template('reset_password.html')

    return reset_password_bp
