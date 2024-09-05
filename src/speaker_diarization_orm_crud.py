from database_session_utils import get_session
from sqlalchemy import Column, Double, Integer, Enum, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class SpeakerDiarization(Base):
    __tablename__ = 'speaker_diarization'

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(Integer, nullable=False)
    speaker = Column(String, nullable=False)
    speaker_diarization_start = Column(Double, nullable=False)
    speaker_diarization_end = Column(Double, nullable=False)

    def __repr__(self):
        return f"<SpeakerDiarization(id={self.id}, segment_id={self.segment_id}, speaker={self.speaker}, speaker_diarization_start={self.speaker_diarization_start}, speaker_diarization_end={self.speaker_diarization_end})>"


def get_speaker_diarization_by_id(id):
    session = get_session()
    speaker_diarization = session.query(SpeakerDiarization).filter(
        SpeakerDiarization.id == id).first()
    session.close()
    return speaker_diarization


def create_speaker_diarization(segment_id, speaker, speaker_diarization_start, speaker_diarization_end):
    session = get_session()
    new_speaker_diarization = SpeakerDiarization(segment_id=segment_id, speaker=speaker,
                                                 speaker_diarization_start=speaker_diarization_start, speaker_diarization_end=speaker_diarization_end)
    session.add(new_speaker_diarization)
    session.commit()
    new_speaker_diarization_id = new_speaker_diarization.id
    session.close()
    return new_speaker_diarization_id


if __name__ == "__main__":
    create_speaker_diarization(1, "trainee", 10, 50)
    print(f"Speaker Diarization with id 1 {get_speaker_diarization_by_id(1)}")
