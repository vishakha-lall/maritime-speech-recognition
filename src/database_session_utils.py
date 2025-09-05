import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url():
    """Construct database URL from environment variables with fallback defaults"""
    db_user = os.getenv('DB_USER', 'aicatsan')
    db_password = os.getenv('DB_PASSWORD', 'aicatsan2024')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'aicatsan')
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def get_session():
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def get_engine():
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    return engine