from database_session_utils import get_session
from sqlalchemy import Column, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Client(Base):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    alias = Column(String, nullable=False)

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, alias={self.alias})>"


def get_client_by_id(id):
    session = get_session()
    client = session.query(Client).filter(
        Client.id == id).first()
    session.close()
    return client


def get_all_clients():
    session = get_session()
    clients = session.query(Client).all()
    session.close()
    return clients


if __name__ == "__main__":
    print(f"All records in table client {get_all_clients()}")
    print(f"Client with id 1 {get_client_by_id(1)}")
