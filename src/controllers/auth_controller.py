from flask import render_template, request, redirect, url_for, session
from flask.views import MethodView
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class LoginController(MethodView):
    def get(self):
        if session.get('logged_in'):
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    def post(self):
        password = request.form.get('password')
        
        if password == "admin123":
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Contraseña incorrecta")

class LogoutController(MethodView):
    def get(self):
        session.clear()
        return redirect(url_for('login'))