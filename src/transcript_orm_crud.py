from database_session_utils import get_session
from sqlalchemy import Column, Integer, Text

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Transcript(Base):
    __tablename__ = 'transcript'

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(Integer, nullable=False)
    speaker_diarization_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Transcript(id={self.id}, segment_id={self.segment_id}, speaker_diarization_id={self.speaker_diarization_id}, text={self.text})>"


def get_transcript_by_id(id):
    session = get_session()
    transcript = session.query(Transcript).filter(
        Transcript.id == id).first()
    session.close()
    return transcript


def create_transcript(segment_id, speaker_diarization_id, text):
    session = get_session()
    session.add(Transcript(segment_id=segment_id, speaker_diarization_id=speaker_diarization_id,
                text=text))
    session.commit()
    session.close()


if __name__ == "__main__":
    create_transcript(1, 1, "tetkdjfksjbgfksjbgfiwhbgfjesbgj")
    print(f"Transcript with id 1 {get_transcript_by_id(1)}")
