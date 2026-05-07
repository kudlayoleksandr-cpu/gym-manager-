import unittest
import tests  # noqa: F401 — triggers path setup

from models.base_model import BaseModel
from models.exercise import Exercise
from models.workout_plan import WorkoutPlan
from models.workout_session import WorkoutSession
from models.user import User


class TestBaseModel(unittest.TestCase):
    def test_to_dict_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            BaseModel().to_dict()


class TestExercise(unittest.TestCase):
    def test_init_required_fields(self):
        ex = Exercise(1, 'Squats', 'legs', 'hard', 4)
        self.assertEqual(ex.id, 1)
        self.assertEqual(ex.name, 'Squats')
        self.assertEqual(ex.muscle_group, 'legs')
        self.assertEqual(ex.difficulty, 'hard')
        self.assertEqual(ex.duration_sets, 4)
        self.assertIsNone(ex.weight)

    def test_init_with_weight(self):
        ex = Exercise(1, 'Squats', 'legs', 'hard', 4, '80')
        self.assertEqual(ex.weight, '80')

    def test_to_dict_contains_all_fields(self):
        ex = Exercise(1, 'Squats', 'legs', 'hard', 4, '80')
        d = ex.to_dict()
        self.assertEqual(d['id'], 1)
        self.assertEqual(d['name'], 'Squats')
        self.assertEqual(d['muscle_group'], 'legs')
        self.assertEqual(d['difficulty'], 'hard')
        self.assertEqual(d['duration_sets'], 4)
        self.assertEqual(d['weight'], '80')

    def test_to_dict_weight_none_by_default(self):
        ex = Exercise(1, 'Squats', 'legs', 'hard', 4)
        self.assertIsNone(ex.to_dict()['weight'])


class TestWorkoutPlan(unittest.TestCase):
    def _make_exercise(self, eid=1, name='Squats'):
        return Exercise(eid, name, 'legs', 'hard', 4)

    def test_init_defaults_to_empty_exercises(self):
        plan = WorkoutPlan(1, 'Leg Day')
        self.assertEqual(plan.exercises, [])

    def test_init_with_exercises(self):
        plan = WorkoutPlan(1, 'Leg Day', [self._make_exercise()])
        self.assertEqual(len(plan.exercises), 1)

    def test_add_exercise(self):
        plan = WorkoutPlan(1, 'Leg Day')
        plan.add_exercise(self._make_exercise())
        self.assertEqual(len(plan.exercises), 1)
        self.assertEqual(plan.exercises[0].name, 'Squats')

    def test_remove_exercise(self):
        ex1 = self._make_exercise(1, 'Squats')
        ex2 = self._make_exercise(2, 'Lunges')
        plan = WorkoutPlan(1, 'Leg Day', [ex1, ex2])
        plan.remove_exercise(1)
        self.assertEqual(len(plan.exercises), 1)
        self.assertEqual(plan.exercises[0].id, 2)

    def test_remove_nonexistent_exercise_is_safe(self):
        plan = WorkoutPlan(1, 'Leg Day', [self._make_exercise()])
        plan.remove_exercise(999)
        self.assertEqual(len(plan.exercises), 1)

    def test_to_dict(self):
        plan = WorkoutPlan(1, 'Leg Day', [self._make_exercise()])
        d = plan.to_dict()
        self.assertEqual(d['id'], 1)
        self.assertEqual(d['name'], 'Leg Day')
        self.assertEqual(len(d['exercises']), 1)


class TestWorkoutSession(unittest.TestCase):
    def _make_session(self):
        return WorkoutSession(1, 1, 'Leg Day', '2026-01-01', 'Squats, Lunges')

    def test_init(self):
        ws = self._make_session()
        self.assertEqual(ws.id, 1)
        self.assertEqual(ws.plan_id, 1)
        self.assertEqual(ws.plan_name, 'Leg Day')
        self.assertEqual(ws.date, '2026-01-01')
        self.assertEqual(ws.order_used, 'Squats, Lunges')

    def test_to_dict(self):
        d = self._make_session().to_dict()
        self.assertEqual(d['id'], 1)
        self.assertEqual(d['plan_name'], 'Leg Day')
        self.assertEqual(d['order_used'], 'Squats, Lunges')


class TestUser(unittest.TestCase):
    def test_init(self):
        user = User(1, 'alice')
        self.assertEqual(user.id, 1)
        self.assertEqual(user.username, 'alice')

    def test_to_dict(self):
        d = User(1, 'alice').to_dict()
        self.assertEqual(d['id'], 1)
        self.assertEqual(d['username'], 'alice')

    def test_is_authenticated(self):
        self.assertTrue(User(1, 'alice').is_authenticated)

    def test_is_active(self):
        self.assertTrue(User(1, 'alice').is_active)

    def test_is_not_anonymous(self):
        self.assertFalse(User(1, 'alice').is_anonymous)

    def test_get_id_returns_string(self):
        self.assertEqual(User(42, 'alice').get_id(), '42')


if __name__ == '__main__':
    unittest.main()
