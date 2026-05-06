import json
import re
import google.generativeai as genai
from models.workout_plan import WorkoutPlan


class AISuggester:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def suggest(self, plan: WorkoutPlan, history: list) -> list[dict]:
        current = [e.name for e in plan.exercises]
        history_str = '; '.join(s.order_used for s in history[-3:]) if history else 'none'

        prompt = (
            f"You are a fitness coach. The user has a workout plan called '{plan.name}'.\n"
            f"Current exercises: {current}\n"
            f"Recent history: {history_str}\n\n"
            "Suggest exactly 4 new exercises that:\n"
            "1. Complement existing ones (same muscle groups, different movements)\n"
            "2. Are NOT already in their plan\n"
            "3. Match the general difficulty of their current exercises\n\n"
            "Return ONLY a valid JSON array, no markdown, no explanation:\n"
            "[\n"
            "  {\n"
            '    "name": "Bulgarian Split Squat",\n'
            '    "muscle_group": "legs",\n'
            '    "difficulty": "hard",\n'
            '    "duration_min": 10,\n'
            '    "reason": "Targets quads and glutes differently than regular squats"\n'
            "  }\n"
            "]"
        )

        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    @staticmethod
    def _parse_json(text: str) -> list[dict]:
        text = text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return json.loads(text.strip())
