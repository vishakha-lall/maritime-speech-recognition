from database_session_utils import get_session
from sqlalchemy import JSON, Column, Enum, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ChecklistItem(Base):
    __tablename__ = 'checklist_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    demanding_event_id = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    importance = Column(Integer, nullable=False)
    tokens = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<ChecklistItem(id={self.id}, demanding_event_id={self.demanding_event_id}, description={self.description}, importance={self.importance}, tokens={self.tokens})>"


def get_checklist_item_by_demanding_event_id(demanding_event_id):
    session = get_session()
    checklist_items = session.query(ChecklistItem).filter(
        ChecklistItem.demanding_event_id == demanding_event_id).all()
    session.close()
    return checklist_items


def get_checklist_item_by_id(id):
    session = get_session()
    checklist_item = session.query(ChecklistItem).filter(
        ChecklistItem.id == id).first()
    session.close()
    return checklist_item


if __name__ == "__main__":
    print(
        f"checklist_items for demanding_event_id 1 {get_checklist_item_by_demanding_event_id(1)}")
