from database_session_utils import get_session
from sqlalchemy import Column, Integer, Enum

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class DemandingEvent(Base):
    __tablename__ = 'demanding_event'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum('Collision Avoidance', 'Main Engine Failure',
                  'Severe Storm', 'Steering Failure', 'Squall', 'Tug Failure', 'Total Black Out', 'Bow Thruster Failure'), nullable=False)
    client_id = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<DemandingEvent(id={self.id}, type={self.type}, client={self.client_id})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'demanding_event': self.type,
            'client_id': self.client_id
        }


def get_demanding_event_by_id(id):
    session = get_session()
    event = session.query(DemandingEvent).filter(
        DemandingEvent.id == id).first()
    session.close()
    return event


def get_demanding_event_by_type_client_id(type, client_id):
    session = get_session()
    event = session.query(DemandingEvent).filter(
        DemandingEvent.type == type, DemandingEvent.client_id == client_id).first()
    session.close()
    return event


def get_all_demanding_events():
    session = get_session()
    events = session.query(DemandingEvent).all()
    session.close()
    return events


def get_all_demanding_events_by_client_id(client_id):
    session = get_session()
    events = session.query(DemandingEvent).filter(DemandingEvent.client_id == client_id).all()
    session.close()
    return events

if __name__ == "__main__":
    print(f"All records in table demanding_event {get_all_demanding_events()}")
    print(f"Demanding event with id 1 {get_demanding_event_by_id(1)}")
    print(
        f"Demanding event with type main_engine_failure and client Cosulich {get_demanding_event_by_type_client_id('main_engine_failure', 1)}")
