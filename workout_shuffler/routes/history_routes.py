from flask import Blueprint, render_template, current_app

history_bp = Blueprint('history', __name__)


def _manager():
    return current_app.config['manager']


@history_bp.route('/history')
def all_history():
    sessions = _manager().get_all_history()
    plan_names = [p.name for p in _manager().get_all_plans()]
    return render_template('history.html', sessions=sessions, plan_names=plan_names, active_plan=None)


@history_bp.route('/history/<name>')
def plan_history(name):
    sessions = _manager().get_history_for(name)
    plan_names = [p.name for p in _manager().get_all_plans()]
    return render_template('history.html', sessions=sessions, plan_names=plan_names, active_plan=name)
