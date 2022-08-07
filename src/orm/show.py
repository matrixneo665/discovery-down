from sqlalchemy import *
from sqlalchemy.orm import relationship
from orm import Base

class Show(Base):
    __tablename__ = 'show'
    id = Column(Integer, primary_key=True)
    slug = Column('Slug', String)
    title = Column('Title', String)
    seasons = relationship("Season", back_populates="show")
    tvdbId = Column('TvdbId', String)