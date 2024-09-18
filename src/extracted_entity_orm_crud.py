from database_session_utils import get_session
from sqlalchemy import Column, Enum, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ExtractedEntity(Base):
    __tablename__ = 'extracted_entity'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    demanding_event_id = Column(Integer, nullable=False)
    segment_id = Column(Integer, nullable=False)
    addressed_entity = Column(String, nullable=False)
    communication_level = Column(Enum('internal', 'external'), nullable=False)

    def __repr__(self):
        return f"<ExtractedEntity(id={self.id}, session_id={self.session_id}, demanding_event_id={self.demanding_event_id}, segment_id={self.segment_id}, addressed_entity={self.addressed_entity}, communication_level={self.communication_level})>"


def get_extracted_entity_by_session_id_demanding_event_id(session_id, demanding_event_id):
    session = get_session()
    extracted_entities = session.query(ExtractedEntity).filter(
        ExtractedEntity.session_id == session_id, ExtractedEntity.demanding_event_id == demanding_event_id).all()
    session.close()
    return extracted_entities


def create_extracted_entities(session_id, demanding_event_id, segment_id_list, addressed_entity_list, communication_level_list):
    session = get_session()
    session.bulk_save_objects([ExtractedEntity(session_id=session_id, demanding_event_id=demanding_event_id, segment_id=segment_id, addressed_entity=addressed_entity,
                              communication_level=communication_level) for (segment_id, addressed_entity, communication_level) in zip(segment_id_list, addressed_entity_list, communication_level_list)])
    session.commit()
    session.close()


if __name__ == "__main__":
    print(
        f"Extracted entities for session_id 1 and demanding_event_id 1 {get_extracted_entity_by_session_id_demanding_event_id(1, 1)}")
    print(
        f"Bulk create extracted entities {create_extracted_entities(1, 1, [1,2,3], ['abc', 'def', 'ghi'], ['internal', 'internal', 'external'])}")
