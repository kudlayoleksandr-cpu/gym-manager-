from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from services.db import UserTable

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def _db():
    return current_app.config['db']


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('plans.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(username) < 3 or len(username) > 80:
            flash('Username must be 3–80 characters.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        db_session = _db().get_session()
        try:
            if db_session.query(UserTable).filter_by(username=username).first():
                flash('Username already taken.', 'error')
                return render_template('register.html')
            if db_session.query(UserTable).filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return render_template('register.html')

            user = UserTable(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db_session.add(user)
            db_session.commit()

            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('plans.index'))
        finally:
            db_session.close()

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('plans.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter username and password.', 'error')
            return render_template('login.html')

        db_session = _db().get_session()
        try:
            user = db_session.query(UserTable).filter_by(username=username).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash('Invalid username or password.', 'error')
                return render_template('login.html')

            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('plans.index'))
        finally:
            db_session.close()

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('auth.login'))
