import sys
import os
import importlib.util

_root = os.path.dirname(os.path.abspath(__file__))
_wdir = os.path.join(_root, 'workout_shuffler')

sys.path.insert(0, _wdir)
os.chdir(_wdir)

_spec = importlib.util.spec_from_file_location('_workout_app', os.path.join(_wdir, 'app.py'))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

create_app = _mod.create_app
app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
