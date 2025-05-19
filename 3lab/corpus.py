from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base

class Corpus(Base):
    __tablename__ = "corpuses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)