from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(32), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    link = Column(String(256), nullable=False)
    category = Column(String(32), nullable=False)
    citations = Column(Integer, default=0)
    is_weekly = Column(Integer, default=0)
    is_yearly = Column(Integer, default=0)
    crawled_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

def get_session():
    engine = create_engine('sqlite:///papers.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session() 