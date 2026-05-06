from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from models.exercise import Exercise

plan_bp = Blueprint('plans', __name__)


def _manager():
    return current_app.config['manager']


def _gemini_key():
    return current_app.config['GEMINI_API_KEY']


@plan_bp.route('/')
def index():
    plans = _manager().get_all_plans()
    return render_template('index.html', plans=plans)


@plan_bp.route('/plan/<name>')
def view_plan(name):
    plan = _manager().get_plan(name)
    if not plan:
        flash('Plan not found.', 'error')
        return redirect(url_for('plans.index'))
    shuffled_order = session.pop('shuffled_order', None)
    shuffle_type = session.pop('shuffle_type', None)
    return render_template('plan.html', plan=plan,
                           shuffled_order=shuffled_order, shuffle_type=shuffle_type)


@plan_bp.route('/plan/create', methods=['POST'])
def create_plan():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Plan name cannot be empty.', 'error')
        return redirect(url_for('plans.index'))
    try:
        _manager().create_plan(name)
        flash(f'Plan "{name}" created!', 'success')
    except Exception:
        flash(f'Plan "{name}" already exists or could not be created.', 'error')
    return redirect(url_for('plans.index'))


@plan_bp.route('/plan/<name>/delete', methods=['POST'])
def delete_plan(name):
    _manager().delete_plan(name)
    flash(f'Plan "{name}" deleted.', 'success')
    return redirect(url_for('plans.index'))


@plan_bp.route('/plan/<name>/add', methods=['POST'])
def add_exercise(name):
    ex_name = request.form.get('name', '').strip()
    if not ex_name:
        flash('Exercise name cannot be empty.', 'error')
        return redirect(url_for('plans.view_plan', name=name))
    muscle = request.form.get('muscle_group', '').strip()
    difficulty = request.form.get('difficulty', 'medium')
    try:
        duration = int(request.form.get('duration_min') or 0)
    except ValueError:
        duration = 0
    exercise = Exercise(None, ex_name, muscle, difficulty, duration)
    _manager().add_exercise(name, exercise)
    flash(f'"{ex_name}" added to {name}.', 'success')
    return redirect(url_for('plans.view_plan', name=name))


@plan_bp.route('/plan/<name>/remove/<int:exercise_id>', methods=['POST'])
def remove_exercise(name, exercise_id):
    _manager().remove_exercise(exercise_id)
    flash('Exercise removed.', 'success')
    return redirect(url_for('plans.view_plan', name=name))


@plan_bp.route('/plan/<name>/shuffle', methods=['POST'])
def shuffle_ai(name):
    from services.ai_shuffler import AIShuffler
    from services.random_shuffler import RandomShuffler

    manager = _manager()
    plan = manager.get_plan(name)
    if not plan:
        flash('Plan not found.', 'error')
        return redirect(url_for('plans.index'))
    if not plan.exercises:
        flash('Add exercises before shuffling.', 'warning')
        return redirect(url_for('plans.view_plan', name=name))

    history = manager.get_history_for(name)
    try:
        order = AIShuffler(_gemini_key()).shuffle(plan, history)
        shuffle_type = 'AI'
    except Exception as e:
        flash(f'AI shuffle failed ({e}) — using random order instead.', 'warning')
        order = RandomShuffler().shuffle(plan, history)
        shuffle_type = 'Random'

    manager.log_session(name, order)
    session['shuffled_order'] = order
    session['shuffle_type'] = shuffle_type
    flash(f'{shuffle_type} shuffle complete! Session logged.', 'success')
    return redirect(url_for('plans.view_plan', name=name))


@plan_bp.route('/plan/<name>/shuffle/random', methods=['POST'])
def shuffle_random(name):
    from services.random_shuffler import RandomShuffler

    manager = _manager()
    plan = manager.get_plan(name)
    if not plan:
        flash('Plan not found.', 'error')
        return redirect(url_for('plans.index'))
    if not plan.exercises:
        flash('Add exercises before shuffling.', 'warning')
        return redirect(url_for('plans.view_plan', name=name))

    history = manager.get_history_for(name)
    order = RandomShuffler().shuffle(plan, history)
    manager.log_session(name, order)
    session['shuffled_order'] = order
    session['shuffle_type'] = 'Random'
    flash('Random shuffle complete! Session logged.', 'success')
    return redirect(url_for('plans.view_plan', name=name))
