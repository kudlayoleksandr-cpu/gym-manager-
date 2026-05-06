from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, event
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class PlanTable(Base):
    __tablename__ = 'plans'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    exercises = relationship('ExerciseTable', back_populates='plan', cascade='all, delete-orphan')


class ExerciseTable(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'))
    name = Column(String, nullable=False)
    muscle_group = Column(String)
    difficulty = Column(String)
    duration_sets = Column(Integer)
    weight = Column(String, nullable=True)
    plan = relationship('PlanTable', back_populates='exercises')


class SessionTable(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey('plans.id'))
    plan_name = Column(String)
    date = Column(String)
    order_used = Column(Text)


class Database:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, connect_args={'check_same_thread': False})
        event.listen(self.engine, 'connect', self._set_pragma)
        self.Session = sessionmaker(bind=self.engine)

    @staticmethod
    def _set_pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)
        self._seed_if_empty()

    def _seed_if_empty(self) -> None:
        session = self.Session()
        try:
            if session.query(PlanTable).count() == 0:
                leg_day = PlanTable(name='Leg Day', exercises=[
                    ExerciseTable(name='Squats',      muscle_group='legs', difficulty='hard',   duration_sets=10),
                    ExerciseTable(name='Lunges',      muscle_group='legs', difficulty='medium', duration_sets=8),
                    ExerciseTable(name='Leg Press',   muscle_group='legs', difficulty='medium', duration_sets=10),
                    ExerciseTable(name='Calf Raises', muscle_group='legs', difficulty='easy',   duration_sets=6),
                ])
                push_day = PlanTable(name='Push Day', exercises=[
                    ExerciseTable(name='Bench Press',    muscle_group='chest',     difficulty='hard',   duration_sets=12),
                    ExerciseTable(name='Shoulder Press', muscle_group='shoulders', difficulty='medium', duration_sets=8),
                    ExerciseTable(name='Tricep Dips',    muscle_group='triceps',   difficulty='medium', duration_sets=7),
                    ExerciseTable(name='Lateral Raises', muscle_group='shoulders', difficulty='easy',   duration_sets=5),
                ])
                session.add_all([leg_day, push_day])
                session.commit()
        finally:
            session.close()

    def get_session(self):
        return self.Session()
