from __future__ import annotations
from datetime import date as dt_date
from models.exercise import Exercise
from models.workout_plan import WorkoutPlan
from models.workout_session import WorkoutSession
from services.db import PlanTable, ExerciseTable, SessionTable


class WorkoutManager:
    def __init__(self, db):
        self.db = db

    def create_plan(self, name: str) -> WorkoutPlan:
        session = self.db.get_session()
        try:
            plan = PlanTable(name=name)
            session.add(plan)
            session.commit()
            return WorkoutPlan(plan.id, plan.name)
        finally:
            session.close()

    def get_plan(self, name: str) -> WorkoutPlan | None:
        session = self.db.get_session()
        try:
            row = session.query(PlanTable).filter_by(name=name).first()
            if not row:
                return None
            exercises = [
                Exercise(e.id, e.name, e.muscle_group, e.difficulty, e.duration_sets)
                for e in row.exercises
            ]
            return WorkoutPlan(row.id, row.name, exercises)
        finally:
            session.close()

    def get_all_plans(self) -> list[WorkoutPlan]:
        session = self.db.get_session()
        try:
            rows = session.query(PlanTable).all()
            return [
                WorkoutPlan(
                    row.id, row.name,
                    [Exercise(e.id, e.name, e.muscle_group, e.difficulty, e.duration_sets)
                     for e in row.exercises]
                )
                for row in rows
            ]
        finally:
            session.close()

    def delete_plan(self, name: str) -> None:
        session = self.db.get_session()
        try:
            row = session.query(PlanTable).filter_by(name=name).first()
            if row:
                session.delete(row)
                session.commit()
        finally:
            session.close()

    def add_exercise(self, plan_name: str, exercise: Exercise) -> Exercise:
        session = self.db.get_session()
        try:
            plan_row = session.query(PlanTable).filter_by(name=plan_name).first()
            if not plan_row:
                raise ValueError(f"Plan '{plan_name}' not found")
            ex = ExerciseTable(
                plan_id=plan_row.id,
                name=exercise.name,
                muscle_group=exercise.muscle_group,
                difficulty=exercise.difficulty,
                duration_sets=exercise.duration_sets,
            )
            session.add(ex)
            session.commit()
            return Exercise(ex.id, ex.name, ex.muscle_group, ex.difficulty, ex.duration_sets)
        finally:
            session.close()

    def remove_exercise(self, exercise_id: int) -> None:
        session = self.db.get_session()
        try:
            ex = session.query(ExerciseTable).filter_by(id=exercise_id).first()
            if ex:
                session.delete(ex)
                session.commit()
        finally:
            session.close()

    def log_session(self, plan_name: str, order_used: list[str]) -> WorkoutSession:
        session = self.db.get_session()
        try:
            plan_row = session.query(PlanTable).filter_by(name=plan_name).first()
            plan_id = plan_row.id if plan_row else None
            ws = SessionTable(
                plan_id=plan_id,
                plan_name=plan_name,
                date=str(dt_date.today()),
                order_used=', '.join(order_used),
            )
            session.add(ws)
            session.commit()
            return WorkoutSession(ws.id, ws.plan_id, ws.plan_name, ws.date, ws.order_used)
        finally:
            session.close()

    def get_all_history(self) -> list[WorkoutSession]:
        session = self.db.get_session()
        try:
            rows = session.query(SessionTable).order_by(SessionTable.id.desc()).all()
            return [
                WorkoutSession(r.id, r.plan_id, r.plan_name, r.date, r.order_used)
                for r in rows
            ]
        finally:
            session.close()

    def get_history_for(self, plan_name: str) -> list[WorkoutSession]:
        session = self.db.get_session()
        try:
            rows = (
                session.query(SessionTable)
                .filter_by(plan_name=plan_name)
                .order_by(SessionTable.id.desc())
                .all()
            )
            return [
                WorkoutSession(r.id, r.plan_id, r.plan_name, r.date, r.order_used)
                for r in rows
            ]
        finally:
            session.close()
