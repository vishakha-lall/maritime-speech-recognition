from database_session_utils import get_session
from sqlalchemy import Column, Double, Integer, Enum

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Segment(Base):
    __tablename__ = 'segment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    demanding_event_id = Column(Integer, nullable=False)
    segment_start = Column(Double, nullable=False)
    segment_end = Column(Double, nullable=False)

    def __repr__(self):
        return f"<Segment(id={self.id}, session_id={self.session_id}, demanding_event_id={self.demanding_event_id}, segment_start={self.segment_start}, segment_end={self.segment_end})>"


def get_segment_by_id(id):
    session = get_session()
    segment = session.query(Segment).filter(
        Segment.id == id).first()
    session.close()
    return segment


def create_segment(session_id, demanding_event_id, segment_start, segment_end):
    session = get_session()
    new_session = Segment(session_id=session_id, demanding_event_id=demanding_event_id,
                          segment_start=segment_start, segment_end=segment_end)
    session.add(new_session)
    session.commit()
    new_session_id = new_session.id
    session.close()
    return new_session_id


def create_segments(session_id, demanding_event_id, segment_start_list, segment_end_list):
    session = get_session()
    session.bulk_save_objects([Segment(session_id=session_id, demanding_event_id=demanding_event_id, segment_start=segment_start,
                              segment_end=segment_end) for (segment_start, segment_end) in zip(segment_start_list, segment_end_list)])
    session.commit()
    session.close()


if __name__ == "__main__":
    print(create_segment(1, 1, 10, 50))
    # create_segments(1,1,[2,3,4],[5,6,7])
    print(f"Segment with id 1 {get_segment_by_id(1)}")
