from flask import Blueprint, render_template, current_app, session
from routes.auth_routes import login_required

history_bp = Blueprint('history', __name__)


def _manager():
    return current_app.config['manager']


def _user_id():
    return session['user_id']


@history_bp.route('/history')
@login_required
def all_history():
    sessions = _manager().get_all_history(_user_id())
    plan_names = [p.name for p in _manager().get_all_plans(_user_id())]
    return render_template('history.html', sessions=sessions, plan_names=plan_names, active_plan=None)


@history_bp.route('/history/<name>')
@login_required
def plan_history(name):
    sessions = _manager().get_history_for(name, _user_id())
    plan_names = [p.name for p in _manager().get_all_plans(_user_id())]
    return render_template('history.html', sessions=sessions, plan_names=plan_names, active_plan=name)
