from database_session_utils import get_session
from sqlalchemy import JSON, Column, Enum, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ChecklistPrompt(Base):
    __tablename__ = 'checklist_prompt'

    id = Column(Integer, primary_key=True, autoincrement=True)
    demanding_event_id = Column(Integer, nullable=False)
    client_id = Column(Integer, nullable=False)
    prompt = Column(String, nullable=False)

    def __repr__(self):
        return f"<ChecklistItem(id={self.id}, demanding_event_id={self.demanding_event_id}, client_id={self.client_id}, prompt={self.prompt})>"


def get_checklist_prompt_by_client_id_demanding_event_id(client_id, demanding_event_id):
    session = get_session()
    checklist_prompt = session.query(ChecklistPrompt).filter(
        ChecklistPrompt.demanding_event_id == demanding_event_id, ChecklistPrompt.client_id == client_id).first()
    session.close()
    return checklist_prompt


if __name__ == "__main__":
    print(
        f"checklist_items for demanding_event_id 1 {get_checklist_prompt_by_client_id_demanding_event_id(1, 1)}")
