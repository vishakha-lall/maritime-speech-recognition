from sqlalchemy import Column, Double, Integer
from database_session_utils import get_session

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class DemandingEventSessionMapping(Base):
    __tablename__ = 'demanding_event_session_mapping'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    demanding_event_id = Column(Integer, nullable=False)
    time_start = Column(Double, nullable=False)
    time_end = Column(Double, nullable=False)

    def __repr__(self):
        return f"<DemandingEventSessionMapping(id={self.id}, session_id={self.session_id}, demanding_event_id={self.demanding_event_id}, time_start={self.time_start}, time_end={self.time_end})>"


def get_demanding_event_session_mapping_by_id(id):
    session = get_session()
    demanding_event_session_mapping = session.query(DemandingEventSessionMapping).filter(
        DemandingEventSessionMapping.id == id).first()
    session.close()
    return demanding_event_session_mapping


def get_demanding_event_session_mapping_by_session_id(session_id):
    session = get_session()
    demanding_event_session_mappings = session.query(DemandingEventSessionMapping).filter(
        DemandingEventSessionMapping.session_id == session_id).all()
    session.close()
    return demanding_event_session_mappings


def get_demanding_event_session_mapping_by_session_id_demanding_event_id(session_id, demanding_event_id):
    session = get_session()
    demanding_event_session_mapping = session.query(DemandingEventSessionMapping).filter(
        DemandingEventSessionMapping.session_id == session_id, DemandingEventSessionMapping.demanding_event_id == demanding_event_id).first()
    session.close()
    return demanding_event_session_mapping


def get_all_demanding_event_session_mappings():
    session = get_session()
    demanding_event_session_mappings = session.query(
        DemandingEventSessionMapping).all()
    session.close()
    return demanding_event_session_mappings


if __name__ == "__main__":
    print(
        f"All records in table demanding_event_session_mapping {get_all_demanding_event_session_mappings()}")
    print(f"Mapping with id 1 {get_demanding_event_session_mapping_by_id(1)}")
    print(
        f"Mapping for session_id 1 demanding_event_id 1 {get_demanding_event_session_mapping_by_session_id(1)}")
