from sqlalchemy import Column, Integer, String, UniqueConstraint
from .db import Base


class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    voter_id = Column(Integer, nullable=False)
    person_id = Column(Integer, nullable=False)
    param = Column(String, nullable=False)
    param_value = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint('voter_id', 'param', 'person_id'), )
