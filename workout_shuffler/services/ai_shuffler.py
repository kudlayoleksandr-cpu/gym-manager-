import json
import re
import google.generativeai as genai
from services.shuffler_base import BaseShuffler
from models.workout_plan import WorkoutPlan


class AIShuffler(BaseShuffler):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def shuffle(self, plan: WorkoutPlan, history: list) -> list[str]:
        exercise_list = [(e.name, e.muscle_group, e.difficulty) for e in plan.exercises]
        total = len(exercise_list)
        replace_count = (total + 1) // 2
        history_str = '; '.join(s.order_used for s in history[-3:]) if history else 'none'

        prompt = (
            f"You are a fitness coach creating a varied workout session.\n"
            f"Plan name: {plan.name}\n"
            f"Current exercises (name, muscle_group, difficulty): {exercise_list}\n"
            f"Recent session history: {history_str}\n\n"
            f"Your task:\n"
            f"1. REPLACE at least {replace_count} out of {total} exercises with DIFFERENT exercises "
            f"that target the same muscle groups and match the same difficulty level.\n"
            f"2. Keep the remaining exercises but reorder everything for maximum effectiveness.\n"
            f"3. Never repeat an exercise from the recent history.\n"
            f"4. Return exactly {total} exercises total.\n\n"
            f"Return ONLY a JSON array of exercise names, nothing else.\n"
            f'Example: ["Romanian Deadlift", "Leg Press", "Squats", "Box Jumps"]'
        )

        response = self.model.generate_content(prompt)
        return self._parse_json(response.text)

    @staticmethod
    def _parse_json(text: str) -> list[str]:
        text = text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return json.loads(text.strip())
