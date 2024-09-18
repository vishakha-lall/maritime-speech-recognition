from database_session_utils import get_session
from sqlalchemy import Boolean, Column, Double, Enum, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ChecklistItemAdherence(Base):
    __tablename__ = 'checklist_item_adherence'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    demanding_event_id = Column(Integer, nullable=False)
    checklist_item_id = Column(Integer, nullable=False)
    is_completed = Column(Boolean, nullable=False)
    completion_time = Column(Double)

    def __repr__(self):
        return f"<ChecklistItemAdherence(id={self.id}, session_id={self.session_id}, demanding_event_id={self.demanding_event_id}, checklist_item_id={self.checklist_item_id}, is_completed={self.is_completed}, completion_time={self.completion_time})>"


def get_checklist_item_aherence_by_session_id_demanding_event_id(session_id, demanding_event_id):
    session = get_session()
    checklist_item_aherences = session.query(ChecklistItemAdherence).filter(
        ChecklistItemAdherence.session_id == session_id, ChecklistItemAdherence.demanding_event_id == demanding_event_id).all()
    session.close()
    return checklist_item_aherences


def create_checklist_item_adherence(session_id, demanding_event_id, checklist_item_id, is_completed, completion_time):
    session = get_session()
    session.add(ChecklistItemAdherence(session_id=session_id, demanding_event_id=demanding_event_id,
                checklist_item_id=checklist_item_id, is_completed=is_completed, completion_time=completion_time))
    session.commit()
    session.close()


if __name__ == "__main__":
    print(
        f"checklist_item_adherence for session_id 1 demanding_event_id 1 {get_checklist_item_aherence_by_session_id_demanding_event_id(1, 1)}")
