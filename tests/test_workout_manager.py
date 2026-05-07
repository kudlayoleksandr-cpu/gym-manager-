import unittest
import tempfile
import os
import tests  # noqa: F401 — triggers path setup

from services.db import Database
from models.workout_manager import WorkoutManager
from models.exercise import Exercise


def _make_manager():
    db_file = tempfile.mktemp(suffix='.db')
    db = Database(f'sqlite:///{db_file}')
    db.init_db()
    return WorkoutManager(db), db_file


class TestUserMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager, cls._db_file = _make_manager()

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls._db_file)
        except OSError:
            pass

    def test_create_user_returns_user(self):
        user = self.manager.create_user('alice', 'password123')
        self.assertEqual(user.username, 'alice')
        self.assertIsNotNone(user.id)

    def test_get_user_by_id(self):
        user = self.manager.create_user('bob', 'password123')
        found = self.manager.get_user_by_id(user.id)
        self.assertEqual(found.username, 'bob')

    def test_get_user_by_id_not_found_returns_none(self):
        self.assertIsNone(self.manager.get_user_by_id(99999))

    def test_get_user_by_username(self):
        self.manager.create_user('carol', 'password123')
        found = self.manager.get_user_by_username('carol')
        self.assertEqual(found.username, 'carol')

    def test_get_user_by_username_not_found_returns_none(self):
        self.assertIsNone(self.manager.get_user_by_username('nobody'))

    def test_check_password_correct(self):
        self.manager.create_user('dave', 'mypassword')
        self.assertTrue(self.manager.check_password('dave', 'mypassword'))

    def test_check_password_wrong_returns_false(self):
        self.manager.create_user('eve', 'mypassword')
        self.assertFalse(self.manager.check_password('eve', 'wrongpassword'))

    def test_check_password_unknown_user_returns_false(self):
        self.assertFalse(self.manager.check_password('ghost', 'password'))


class TestPlanMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager, cls._db_file = _make_manager()
        cls.user = cls.manager.create_user('planuser', 'password123')
        cls.other = cls.manager.create_user('otheruser', 'password123')

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls._db_file)
        except OSError:
            pass

    def test_create_plan(self):
        plan = self.manager.create_plan('Leg Day', self.user.id)
        self.assertEqual(plan.name, 'Leg Day')
        self.assertIsNotNone(plan.id)

    def test_get_plan_found(self):
        self.manager.create_plan('Push Day', self.user.id)
        plan = self.manager.get_plan('Push Day', self.user.id)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.name, 'Push Day')

    def test_get_plan_not_found_returns_none(self):
        self.assertIsNone(self.manager.get_plan('Nonexistent', self.user.id))

    def test_get_plan_wrong_user_returns_none(self):
        self.manager.create_plan('Pull Day', self.user.id)
        self.assertIsNone(self.manager.get_plan('Pull Day', self.other.id))

    def test_get_all_plans_only_own(self):
        self.manager.create_plan('My Plan', self.user.id)
        self.manager.create_plan('Their Plan', self.other.id)
        names = [p.name for p in self.manager.get_all_plans(self.user.id)]
        self.assertIn('My Plan', names)
        self.assertNotIn('Their Plan', names)

    def test_delete_plan(self):
        self.manager.create_plan('Delete Me', self.user.id)
        self.manager.delete_plan('Delete Me', self.user.id)
        self.assertIsNone(self.manager.get_plan('Delete Me', self.user.id))

    def test_delete_plan_wrong_user_does_nothing(self):
        self.manager.create_plan('Safe Plan', self.user.id)
        self.manager.delete_plan('Safe Plan', self.other.id)
        self.assertIsNotNone(self.manager.get_plan('Safe Plan', self.user.id))

    def test_deleted_plan_exercises_removed(self):
        self.manager.create_plan('With Exercises', self.user.id)
        ex = Exercise(None, 'Squats', 'legs', 'hard', 4)
        self.manager.add_exercise('With Exercises', ex, self.user.id)
        self.manager.delete_plan('With Exercises', self.user.id)
        self.assertIsNone(self.manager.get_plan('With Exercises', self.user.id))


class TestExerciseMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager, cls._db_file = _make_manager()
        cls.user = cls.manager.create_user('exuser', 'password123')
        cls.manager.create_plan('Workout', cls.user.id)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls._db_file)
        except OSError:
            pass

    def test_add_exercise_returns_exercise(self):
        ex = Exercise(None, 'Squats', 'legs', 'hard', 4, '80')
        result = self.manager.add_exercise('Workout', ex, self.user.id)
        self.assertEqual(result.name, 'Squats')
        self.assertEqual(result.weight, '80')
        self.assertIsNotNone(result.id)

    def test_add_exercise_appears_in_plan(self):
        ex = Exercise(None, 'Lunges', 'legs', 'medium', 3)
        self.manager.add_exercise('Workout', ex, self.user.id)
        plan = self.manager.get_plan('Workout', self.user.id)
        self.assertIn('Lunges', [e.name for e in plan.exercises])

    def test_add_exercise_optional_weight_is_none(self):
        ex = Exercise(None, 'Calf Raises', 'legs', 'easy', 3)
        result = self.manager.add_exercise('Workout', ex, self.user.id)
        self.assertIsNone(result.weight)

    def test_remove_exercise(self):
        ex = Exercise(None, 'Leg Press', 'legs', 'medium', 3)
        added = self.manager.add_exercise('Workout', ex, self.user.id)
        self.manager.remove_exercise(added.id)
        plan = self.manager.get_plan('Workout', self.user.id)
        self.assertNotIn(added.id, [e.id for e in plan.exercises])


class TestSessionMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager, cls._db_file = _make_manager()
        cls.user = cls.manager.create_user('sessuser', 'password123')
        cls.other = cls.manager.create_user('other_sess', 'password123')
        cls.manager.create_plan('Session Plan', cls.user.id)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls._db_file)
        except OSError:
            pass

    def test_log_session(self):
        ws = self.manager.log_session('Session Plan', ['Squats', 'Lunges'], self.user.id)
        self.assertEqual(ws.plan_name, 'Session Plan')
        self.assertIn('Squats', ws.order_used)

    def test_get_all_history_returns_sessions(self):
        self.manager.log_session('Session Plan', ['A', 'B'], self.user.id)
        history = self.manager.get_all_history(self.user.id)
        self.assertGreater(len(history), 0)

    def test_get_all_history_isolated_per_user(self):
        history = self.manager.get_all_history(self.other.id)
        self.assertEqual(len(history), 0)

    def test_get_history_for_returns_only_that_plan(self):
        self.manager.log_session('Session Plan', ['X', 'Y'], self.user.id)
        history = self.manager.get_history_for('Session Plan', self.user.id)
        self.assertTrue(all(h.plan_name == 'Session Plan' for h in history))

    def test_get_history_for_wrong_user_returns_empty(self):
        history = self.manager.get_history_for('Session Plan', self.other.id)
        self.assertEqual(len(history), 0)


if __name__ == '__main__':
    unittest.main()
