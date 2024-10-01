from sqlalchemy import Column, Date, Integer
from database_session_utils import get_session

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Session(Base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    subject_id = Column(Integer, nullable=False)
    exercise_id = Column(Integer, nullable=False)
    client_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Session(id={self.id}, date={self.date}, subject_id={self.subject_id}, exercise_id={self.exercise_id}, client_id={self.client_id})>"


def get_session_by_id(id):
    session = get_session()
    recording_session = session.query(Session).filter(
        Session.id == id).first()
    session.close()
    return recording_session


def get_session_by_date_subject_id_exercise_id_client_id(date, subject_id, exercise_id, client_id):
    session = get_session()
    recording_session = session.query(Session).filter(Session.date == date, Session.subject_id ==
                                                      subject_id, Session.exercise_id == exercise_id, Session.client_id == client_id).first()
    session.close()
    return recording_session


def get_session_by_subject_id_exercise_id(subject_id, exercise_id):
    session = get_session()
    recording_session = session.query(Session).filter(
        Session.subject_id == subject_id, Session.exercise_id == exercise_id).first()
    session.close()
    return recording_session


def get_sessions_by_subject_id(subject_id):
    session = get_session()
    recording_sessions = session.query(Session).filter(Session.subject_id == subject_id).all()
    session.close()
    return recording_sessions

 
def get_all_sessions():
    session = get_session()
    recording_sessions = session.query(Session).all()
    session.close()
    return recording_sessions


if __name__ == "__main__":
    print(f"All records in table session {get_all_sessions()}")
    print(f"Recording session with id 0 {get_session_by_id(0)}")
    print(
        f"Recording session with date '2023-08-14' subject_id 1 exercise_id 1 client_id 1 {get_session_by_date_subject_id_exercise_id_client_id('2023-08-14', 1,1,1)}")
