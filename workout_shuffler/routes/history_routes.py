from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user

history_bp = Blueprint('history', __name__)


def _manager():
    return current_app.config['manager']


@history_bp.route('/history')
@login_required
def all_history():
    sessions = _manager().get_all_history(current_user.id)
    plan_names = [p.name for p in _manager().get_all_plans(current_user.id)]
    return render_template('history.html', sessions=sessions, plan_names=plan_names, active_plan=None)


@history_bp.route('/history/<name>')
@login_required
def plan_history(name):
    sessions = _manager().get_history_for(name, current_user.id)
    plan_names = [p.name for p in _manager().get_all_plans(current_user.id)]
    return render_template('history.html', sessions=sessions, plan_names=plan_names, active_plan=name)
