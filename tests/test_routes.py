import unittest
import tempfile
import os
import uuid
import tests  # noqa: F401 — triggers path setup


def _create_app(db_file):
    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['DEBUG'] = 'false'
    from app import create_app
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    return flask_app


class TestAuthRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._db_file = tempfile.mktemp(suffix='.db')
        cls.flask_app = _create_app(cls._db_file)
        cls.manager = cls.flask_app.config['manager']

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls._db_file)
        except OSError:
            pass

    def setUp(self):
        self.client = self.flask_app.test_client()

    def _uid(self):
        return f'u_{uuid.uuid4().hex[:8]}'

    def test_register_page_returns_200(self):
        self.assertEqual(self.client.get('/register').status_code, 200)

    def test_register_page_contains_form(self):
        self.assertIn(b'Register', self.client.get('/register').data)

    def test_login_page_returns_200(self):
        self.assertEqual(self.client.get('/login').status_code, 200)

    def test_register_creates_user_and_redirects(self):
        username = self._uid()
        resp = self.client.post('/register',
                                data={'username': username, 'password': 'password123'},
                                follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIsNotNone(self.manager.get_user_by_username(username))

    def test_register_duplicate_username_shows_error(self):
        username = self._uid()
        self.client.post('/register', data={'username': username, 'password': 'pass123'})
        resp = self.client.post('/register',
                                data={'username': username, 'password': 'pass123'},
                                follow_redirects=True)
        self.assertIn(b'already taken', resp.data)

    def test_register_short_password_shows_error(self):
        resp = self.client.post('/register',
                                data={'username': self._uid(), 'password': '123'},
                                follow_redirects=True)
        self.assertIn(b'6 characters', resp.data)

    def test_register_empty_username_shows_error(self):
        resp = self.client.post('/register',
                                data={'username': '', 'password': 'password123'},
                                follow_redirects=True)
        self.assertIn(b'required', resp.data)

    def test_login_valid_credentials_redirects(self):
        username = self._uid()
        self.manager.create_user(username, 'password123')
        resp = self.client.post('/login',
                                data={'username': username, 'password': 'password123'},
                                follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

    def test_login_invalid_credentials_shows_error(self):
        resp = self.client.post('/login',
                                data={'username': 'nobody', 'password': 'wrongpass'},
                                follow_redirects=True)
        self.assertIn(b'Invalid', resp.data)

    def test_logout_redirects_to_login(self):
        username = self._uid()
        self.manager.create_user(username, 'password123')
        self.client.post('/login', data={'username': username, 'password': 'password123'})
        resp = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(b'login', resp.headers['Location'].lower().encode())

    def test_protected_route_redirects_when_not_logged_in(self):
        c = self.flask_app.test_client()
        resp = c.get('/', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])


class TestPlanRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._db_file = tempfile.mktemp(suffix='.db')
        cls.flask_app = _create_app(cls._db_file)
        cls.manager = cls.flask_app.config['manager']
        cls._username = f'planroute_{uuid.uuid4().hex[:6]}'
        cls.manager.create_user(cls._username, 'password123')

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls._db_file)
        except OSError:
            pass

    def setUp(self):
        self.client = self.flask_app.test_client()
        self.client.post('/login', data={
            'username': self._username, 'password': 'password123'
        })

    def _plan(self):
        return f'Plan_{uuid.uuid4().hex[:6]}'

    def test_index_loads_when_logged_in(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_create_plan_appears_on_homepage(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        resp = self.client.get('/', follow_redirects=True)
        self.assertIn(name.encode(), resp.data)

    def test_create_plan_empty_name_shows_error(self):
        resp = self.client.post('/plan/create', data={'name': ''},
                                follow_redirects=True)
        self.assertIn(b'cannot be empty', resp.data)

    def test_view_plan_returns_200(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        self.assertEqual(self.client.get(f'/plan/{name}').status_code, 200)

    def test_view_nonexistent_plan_redirects(self):
        resp = self.client.get('/plan/DoesNotExist999', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

    def test_add_exercise_shows_in_plan(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        self.client.post(f'/plan/{name}/add', data={
            'name': 'Squats', 'muscle_group': 'legs',
            'difficulty': 'hard', 'duration_sets': '4',
        })
        self.assertIn(b'Squats', self.client.get(f'/plan/{name}').data)

    def test_add_exercise_empty_name_shows_error(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        resp = self.client.post(f'/plan/{name}/add',
                                data={'name': '', 'muscle_group': 'legs',
                                      'difficulty': 'hard', 'duration_sets': '4'},
                                follow_redirects=True)
        self.assertIn(b'cannot be empty', resp.data)

    def test_remove_exercise(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        self.client.post(f'/plan/{name}/add', data={
            'name': 'Lunges', 'muscle_group': 'legs',
            'difficulty': 'medium', 'duration_sets': '3',
        })
        user = self.manager.get_user_by_username(self._username)
        plan = self.manager.get_plan(name, user.id)
        ex_id = plan.exercises[0].id
        resp = self.client.post(f'/plan/{name}/remove/{ex_id}',
                                follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_delete_plan_removes_from_list(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        self.client.post(f'/plan/{name}/delete', follow_redirects=True)
        resp = self.client.get('/')
        self.assertNotIn(name.encode(), resp.data)

    def test_random_shuffle_returns_200(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        for ex_name in ['Squats', 'Lunges', 'Leg Press']:
            self.client.post(f'/plan/{name}/add', data={
                'name': ex_name, 'muscle_group': 'legs',
                'difficulty': 'medium', 'duration_sets': '3',
            })
        resp = self.client.post(f'/plan/{name}/shuffle/random',
                                follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_random_shuffle_empty_plan_shows_warning(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})
        resp = self.client.post(f'/plan/{name}/shuffle/random',
                                follow_redirects=True)
        self.assertIn(b'exercises before shuffling', resp.data)

    def test_plan_belongs_to_user_only(self):
        name = self._plan()
        self.client.post('/plan/create', data={'name': name})

        other_username = f'other_{uuid.uuid4().hex[:6]}'
        self.manager.create_user(other_username, 'password123')
        other_client = self.flask_app.test_client()
        other_client.post('/login', data={
            'username': other_username, 'password': 'password123'
        })
        resp = other_client.get(f'/plan/{name}', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)


if __name__ == '__main__':
    unittest.main()
