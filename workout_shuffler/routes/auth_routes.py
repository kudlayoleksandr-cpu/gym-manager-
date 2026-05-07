from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint('auth', __name__)


def _manager():
    return current_app.config['manager']


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')
        if _manager().get_user_by_username(username):
            flash('Username already taken.', 'error')
            return render_template('register.html')
        user = _manager().create_user(username, password)
        login_user(user)
        flash(f'Welcome, {username}!', 'success')
        return redirect(url_for('plans.index'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if _manager().check_password(username, password):
            user = _manager().get_user_by_username(username)
            login_user(user)
            return redirect(url_for('plans.index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
