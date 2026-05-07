from __future__ import annotations
from datetime import date as dt_date
from werkzeug.security import generate_password_hash, check_password_hash
from models.exercise import Exercise
from models.workout_plan import WorkoutPlan
from models.workout_session import WorkoutSession
from models.user import User
from services.db import PlanTable, ExerciseTable, SessionTable, UserTable


class WorkoutManager:
    def __init__(self, db):
        self.db = db

    # ── User ──────────────────────────────────────────────────────────────

    def create_user(self, username: str, password: str) -> User:
        session = self.db.get_session()
        try:
            row = UserTable(username=username, password_hash=generate_password_hash(password))
            session.add(row)
            session.commit()
            return User(row.id, row.username)
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> User | None:
        session = self.db.get_session()
        try:
            row = session.query(UserTable).filter_by(id=user_id).first()
            return User(row.id, row.username) if row else None
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> User | None:
        session = self.db.get_session()
        try:
            row = session.query(UserTable).filter_by(username=username).first()
            return User(row.id, row.username) if row else None
        finally:
            session.close()

    def check_password(self, username: str, password: str) -> bool:
        session = self.db.get_session()
        try:
            row = session.query(UserTable).filter_by(username=username).first()
            return bool(row and check_password_hash(row.password_hash, password))
        finally:
            session.close()

    # ── Plans ─────────────────────────────────────────────────────────────

    def create_plan(self, name: str, user_id: int) -> WorkoutPlan:
        session = self.db.get_session()
        try:
            plan = PlanTable(name=name, user_id=user_id)
            session.add(plan)
            session.commit()
            return WorkoutPlan(plan.id, plan.name)
        finally:
            session.close()

    def get_plan(self, name: str, user_id: int) -> WorkoutPlan | None:
        session = self.db.get_session()
        try:
            row = session.query(PlanTable).filter_by(name=name, user_id=user_id).first()
            if not row:
                return None
            exercises = [
                Exercise(e.id, e.name, e.muscle_group, e.difficulty, e.duration_sets, e.weight)
                for e in row.exercises
            ]
            return WorkoutPlan(row.id, row.name, exercises)
        finally:
            session.close()

    def get_all_plans(self, user_id: int) -> list[WorkoutPlan]:
        session = self.db.get_session()
        try:
            rows = session.query(PlanTable).filter_by(user_id=user_id).all()
            return [
                WorkoutPlan(
                    row.id, row.name,
                    [Exercise(e.id, e.name, e.muscle_group, e.difficulty, e.duration_sets, e.weight)
                     for e in row.exercises]
                )
                for row in rows
            ]
        finally:
            session.close()

    def delete_plan(self, name: str, user_id: int) -> None:
        session = self.db.get_session()
        try:
            row = session.query(PlanTable).filter_by(name=name, user_id=user_id).first()
            if row:
                session.delete(row)
                session.commit()
        finally:
            session.close()

    # ── Exercises ─────────────────────────────────────────────────────────

    def add_exercise(self, plan_name: str, exercise: Exercise, user_id: int) -> Exercise:
        session = self.db.get_session()
        try:
            plan_row = session.query(PlanTable).filter_by(name=plan_name, user_id=user_id).first()
            if not plan_row:
                raise ValueError(f"Plan '{plan_name}' not found")
            ex = ExerciseTable(
                plan_id=plan_row.id,
                name=exercise.name,
                muscle_group=exercise.muscle_group,
                difficulty=exercise.difficulty,
                duration_sets=exercise.duration_sets,
                weight=exercise.weight,
            )
            session.add(ex)
            session.commit()
            return Exercise(ex.id, ex.name, ex.muscle_group, ex.difficulty, ex.duration_sets, ex.weight)
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

    # ── Sessions ──────────────────────────────────────────────────────────

    def log_session(self, plan_name: str, order_used: list[str], user_id: int) -> WorkoutSession:
        session = self.db.get_session()
        try:
            plan_row = session.query(PlanTable).filter_by(name=plan_name, user_id=user_id).first()
            ws = SessionTable(
                plan_id=plan_row.id if plan_row else None,
                plan_name=plan_name,
                user_id=user_id,
                date=str(dt_date.today()),
                order_used=', '.join(order_used),
            )
            session.add(ws)
            session.commit()
            return WorkoutSession(ws.id, ws.plan_id, ws.plan_name, ws.date, ws.order_used)
        finally:
            session.close()

    def get_all_history(self, user_id: int) -> list[WorkoutSession]:
        session = self.db.get_session()
        try:
            rows = session.query(SessionTable).filter_by(user_id=user_id).order_by(SessionTable.id.desc()).all()
            return [WorkoutSession(r.id, r.plan_id, r.plan_name, r.date, r.order_used) for r in rows]
        finally:
            session.close()

    def get_history_for(self, plan_name: str, user_id: int) -> list[WorkoutSession]:
        session = self.db.get_session()
        try:
            rows = (
                session.query(SessionTable)
                .filter_by(plan_name=plan_name, user_id=user_id)
                .order_by(SessionTable.id.desc())
                .all()
            )
            return [WorkoutSession(r.id, r.plan_id, r.plan_name, r.date, r.order_used) for r in rows]
        finally:
            session.close()
