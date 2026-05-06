import json
import re
import google.generativeai as genai
from services.shuffler_base import BaseShuffler
from models.workout_plan import WorkoutPlan


class AIShuffler(BaseShuffler):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def shuffle(self, plan: WorkoutPlan, history: list) -> list[str]:
        exercise_list = [e.name for e in plan.exercises]
        history_str = '; '.join(s.order_used for s in history[-3:]) if history else 'none'

        prompt = (
            "You are a fitness coach. Reorder these exercises for maximum effectiveness "
            "and to avoid muscle fatigue.\n"
            f"Plan name: {plan.name}\n"
            f"Exercises: {exercise_list}\n"
            f"Recent session history (avoid repeating same order): {history_str}\n"
            "Return ONLY a JSON array of exercise names in the new order, nothing else.\n"
            'Example: ["Lunges", "Leg Press", "Squats", "Calf Raises"]'
        )

        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    @staticmethod
    def _parse_json(text: str) -> list[str]:
        text = text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return json.loads(text.strip())
