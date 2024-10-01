from database_session_utils import get_session
from sqlalchemy import Column, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Subject(Base):
    __tablename__ = 'subject'

    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(String, nullable=False)
    client_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Subject(id={self.id}, alias={self.alias}, client_id={self.client_id})>"

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.alias,
            'client_id': self.client_id
        }
    
def get_subject_by_id(id):
    session = get_session()
    subject = session.query(Subject).filter(
        Subject.id == id).first()
    session.close()
    return subject


def get_subject_by_alias(alias):
    session = get_session()
    subject = session.query(Subject).filter(
        Subject.alias == alias
    ).first()
    session.close()
    return subject


def get_all_subjects():
    session = get_session()
    subjects = session.query(Subject).all()
    session.close()
    return subjects


def get_all_subjects_by_client_id(client_id):
    session = get_session()
    subjects = session.query(Subject).filter(
        Subject.client_id == client_id).all()
    session.close()
    return subjects


if __name__ == "__main__":
    print(f"All records in table subject {get_all_subjects()}")
    print(f"Subject with id 1 {get_subject_by_id(1)}")
    print(f"Subject with alias cos01 {get_subject_by_alias('cos01')}")
    print(f"Subjects with client_id 1 {get_all_subjects_by_client_id(1)}")
