from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker


def get_session():
    DATABASE_URL = "mysql+pymysql://aicatsan:aicatsan2024@localhost:3306/aicatsan"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

def get_engine():
    DATABASE_URL = "mysql+pymysql://aicatsan:aicatsan2024@localhost:3306/aicatsan"
    engine = create_engine(DATABASE_URL)
    return engine