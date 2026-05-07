from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from models.exercise import Exercise
from routes.auth_routes import login_required

suggestion_bp = Blueprint('suggestions', __name__)


def _manager():
    return current_app.config['manager']


def _gemini_key():
    return current_app.config['GEMINI_API_KEY']


def _user_id():
    return session['user_id']


@suggestion_bp.route('/plan/<name>/suggest')
@login_required
def suggest(name):
    from services.ai_suggester import AISuggester

    manager = _manager()
    plan = manager.get_plan(name, _user_id())
    if not plan:
        flash('Plan not found.', 'error')
        return redirect(url_for('plans.index'))

    history = manager.get_history_for(name, _user_id())
    try:
        suggestions = AISuggester(_gemini_key()).suggest(plan, history)
    except Exception as e:
        flash(f'AI suggestions failed: {e}', 'error')
        suggestions = []

    return render_template('suggest.html', plan=plan, suggestions=suggestions)


@suggestion_bp.route('/plan/<name>/suggest/add', methods=['POST'])
@login_required
def add_suggestion(name):
    ex_name = request.form.get('name', '').strip()
    muscle = request.form.get('muscle_group', '').strip()
    difficulty = request.form.get('difficulty', 'medium')
    try:
        duration = int(request.form.get('duration_min') or 0)
    except ValueError:
        duration = 0

    exercise = Exercise(None, ex_name, muscle, difficulty, duration)
    _manager().add_exercise(name, exercise, _user_id())
    flash(f'"{ex_name}" added to {name}!', 'success')
    return redirect(url_for('plans.view_plan', name=name))
