from datetime import datetime, timedelta
from flask import session, redirect, url_for
from functools import wraps

SESSION_TIMEOUT = timedelta(minutes=5)

def init_session_timeout(app):
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = SESSION_TIMEOUT
        session.modified = True
        session['last_activity'] = datetime.utcnow().isoformat()

def check_session_timeout(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.utcnow() - last_activity > SESSION_TIMEOUT:
                session.clear()
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function