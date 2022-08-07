from sqlalchemy import *
from sqlalchemy.orm import relationship
from orm import Base

class Season(Base):
    __tablename__ = 'season'
    id = Column(Integer, primary_key=True)
    num = Column('Num', Integer)
    episodes = relationship("Episode", back_populates="season")
    showId = Column('ShowId', Integer, ForeignKey("show.id"))
    show = relationship("Show", back_populates="seasons")