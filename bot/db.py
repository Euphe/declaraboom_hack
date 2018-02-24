import time
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = None
session_maker = sessionmaker(autocommit=False, autoflush=False)
db_session_factory = scoped_session(session_maker)
Base = declarative_base()

session = None

def init_db(db_uri):
    global engine
    time.sleep(4)
    engine = create_engine(db_uri, convert_unicode=True)
    session_maker.configure(bind=engine)

    from . import models
    Base.metadata.create_all(bind=engine)

def get_session():
    global session
    if not session:
        session = db_session_factory()
    return session

def close_session(func, *args, **kwargs):
    def wraps(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        finally:
            if session:
                session.close()

        return result
    return wraps
