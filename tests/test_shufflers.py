import unittest
from unittest.mock import MagicMock, patch
import tests  # noqa: F401 — triggers path setup

from models.exercise import Exercise
from models.workout_plan import WorkoutPlan
from services.random_shuffler import RandomShuffler
from services.ai_shuffler import AIShuffler
from services.ai_suggester import AISuggester


def _make_plan(names=None):
    names = names or ['Squats', 'Lunges', 'Leg Press', 'Calf Raises']
    exercises = [
        Exercise(i, name, 'legs', 'medium', 3)
        for i, name in enumerate(names, 1)
    ]
    return WorkoutPlan(1, 'Leg Day', exercises)


class TestRandomShuffler(unittest.TestCase):
    def test_returns_all_exercise_names(self):
        plan = _make_plan()
        result = RandomShuffler().shuffle(plan, [])
        self.assertEqual(set(result), {'Squats', 'Lunges', 'Leg Press', 'Calf Raises'})

    def test_returns_same_count(self):
        plan = _make_plan()
        self.assertEqual(len(RandomShuffler().shuffle(plan, [])), 4)

    def test_returns_list_of_strings(self):
        result = RandomShuffler().shuffle(_make_plan(), [])
        self.assertTrue(all(isinstance(r, str) for r in result))

    def test_history_parameter_ignored(self):
        plan = _make_plan()
        history = [MagicMock(order_used='Squats, Lunges, Leg Press, Calf Raises')]
        result = RandomShuffler().shuffle(plan, history)
        self.assertEqual(len(result), 4)

    def test_single_exercise_plan(self):
        plan = _make_plan(['Squats'])
        result = RandomShuffler().shuffle(plan, [])
        self.assertEqual(result, ['Squats'])

    def test_empty_plan(self):
        plan = WorkoutPlan(1, 'Empty')
        result = RandomShuffler().shuffle(plan, [])
        self.assertEqual(result, [])


class TestAIShufflerParseJson(unittest.TestCase):
    def test_plain_json_array(self):
        result = AIShuffler._parse_json('["Squats", "Lunges", "Leg Press"]')
        self.assertEqual(result, ['Squats', 'Lunges', 'Leg Press'])

    def test_strips_json_markdown_block(self):
        result = AIShuffler._parse_json('```json\n["Squats", "Lunges"]\n```')
        self.assertEqual(result, ['Squats', 'Lunges'])

    def test_strips_plain_code_block(self):
        result = AIShuffler._parse_json('```\n["Squats"]\n```')
        self.assertEqual(result, ['Squats'])

    def test_strips_surrounding_whitespace(self):
        result = AIShuffler._parse_json('  ["Squats", "Lunges"]  ')
        self.assertEqual(result, ['Squats', 'Lunges'])

    def test_invalid_json_raises(self):
        with self.assertRaises(Exception):
            AIShuffler._parse_json('not valid json')

    def test_returns_list(self):
        result = AIShuffler._parse_json('["A", "B"]')
        self.assertIsInstance(result, list)


class TestAISuggesterParseJson(unittest.TestCase):
    def test_plain_json_array_of_dicts(self):
        json_str = '[{"name": "Bulgarian Split Squat", "muscle_group": "legs", "difficulty": "hard", "duration_sets": 3, "reason": "test"}]'
        result = AISuggester._parse_json(json_str)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Bulgarian Split Squat')

    def test_strips_markdown_block(self):
        json_str = '```json\n[{"name": "Box Jumps", "muscle_group": "legs", "difficulty": "hard", "duration_sets": 3, "reason": "test"}]\n```'
        result = AISuggester._parse_json(json_str)
        self.assertEqual(result[0]['name'], 'Box Jumps')

    def test_invalid_json_raises(self):
        with self.assertRaises(Exception):
            AISuggester._parse_json('not valid json')


class TestAIShufflerShuffle(unittest.TestCase):
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_returns_parsed_model_response(self, _mock_cfg, mock_model_cls):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = '["Lunges", "Squats", "Leg Press", "Calf Raises"]'
        mock_model_cls.return_value = mock_model

        result = AIShuffler('fake-key').shuffle(_make_plan(), [])
        self.assertEqual(result, ['Lunges', 'Squats', 'Leg Press', 'Calf Raises'])

    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_prompt_includes_exercise_names(self, _mock_cfg, mock_model_cls):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = '["Squats", "Lunges"]'
        mock_model_cls.return_value = mock_model

        AIShuffler('fake-key').shuffle(_make_plan(['Squats', 'Lunges']), [])
        prompt = mock_model.generate_content.call_args[0][0]
        self.assertIn('Squats', prompt)
        self.assertIn('Lunges', prompt)

    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_prompt_includes_history(self, _mock_cfg, mock_model_cls):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = '["Squats", "Lunges"]'
        mock_model_cls.return_value = mock_model

        history = [MagicMock(order_used='Squats, Lunges, Leg Press')]
        AIShuffler('fake-key').shuffle(_make_plan(['Squats', 'Lunges']), history)
        prompt = mock_model.generate_content.call_args[0][0]
        self.assertIn('Squats, Lunges, Leg Press', prompt)

    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_no_history_uses_none_string(self, _mock_cfg, mock_model_cls):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = '["Squats", "Lunges"]'
        mock_model_cls.return_value = mock_model

        AIShuffler('fake-key').shuffle(_make_plan(['Squats', 'Lunges']), [])
        prompt = mock_model.generate_content.call_args[0][0]
        self.assertIn('none', prompt)


if __name__ == '__main__':
    unittest.main()
