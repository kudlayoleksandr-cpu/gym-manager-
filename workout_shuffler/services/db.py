from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, UniqueConstraint, event
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class UserTable(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    plans = relationship('PlanTable', back_populates='user', cascade='all, delete-orphan')


class PlanTable(Base):
    __tablename__ = 'plans'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    user = relationship('UserTable', back_populates='plans')
    exercises = relationship('ExerciseTable', back_populates='plan', cascade='all, delete-orphan')
    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_user_plan_name'),)


class ExerciseTable(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'))
    name = Column(String, nullable=False)
    muscle_group = Column(String)
    difficulty = Column(String)
    duration_min = Column(Integer)
    plan = relationship('PlanTable', back_populates='exercises')


class SessionTable(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey('plans.id'))
    plan_name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(String)
    order_used = Column(Text)


class Database:
    def __init__(self, db_url: str):
        kwargs = {}
        if db_url.startswith('sqlite'):
            kwargs['connect_args'] = {'check_same_thread': False}
        self.engine = create_engine(db_url, **kwargs)
        if db_url.startswith('sqlite'):
            event.listen(self.engine, 'connect', self._set_pragma)
        self.Session = sessionmaker(bind=self.engine)

    @staticmethod
    def _set_pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()
