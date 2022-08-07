from sqlalchemy import *
from sqlalchemy.orm import relationship
#from .common import Base
from orm import Base

class Episode(Base):
    __tablename__ = 'episode'
    id = Column(Integer, primary_key=True)
    title = Column('Title', String)
    num = Column('Num', Integer)
    isDownloaded = Column('IsDownloaded', Boolean, default = False)
    airDate = Column('AirDate', DateTime)
    publishDate = Column('PublishDate', DateTime)
    licenseUrl = Column('LicenseUrl', String)
    drmToken = Column('DRMToken', String)
    drmEnabled = Column('DRMEnabled', Boolean, default = False)
    seasonId = Column(Integer, ForeignKey("season.id"))
    season = relationship("Season", back_populates="episodes")
    videoData = relationship("VideoData", back_populates="episode")
    audioData = relationship("AudioData", back_populates="episode")
    captionData = relationship('CaptionData', back_populates='episode')

class VideoData(Base):
    __tablename__ = "VideoData"
    id = Column(Integer, primary_key=True)
    streamId = Column('StreamId', String)
    streamUrl = Column('StreamUrl', String)
    pssh = Column('Pssh', String, default = '')
    key = Column('Key', String, default = '')
    bandwidth = Column('Bandwidth', String, default = '')
    width = Column('Width', Integer)
    height = Column('Height', Integer)
    numPeriods = Column('NumPeriods', Integer)
    episodeId = Column(Integer, ForeignKey("episode.id"))
    episode = relationship("Episode", back_populates="videoData")

class AudioData(Base):
    __tablename__ = "AudioData"
    id = Column(Integer, primary_key=True)
    streamId = Column('StreamId', String)
    streamUrl = Column('StreamUrl', String)
    pssh = Column('Pssh', String, default = '')
    key = Column('Key', String, default = '')
    bandwidth = Column('Bandwidth', String, default = '')
    episodeId = Column(Integer, ForeignKey("episode.id"))
    episode = relationship("Episode", back_populates="audioData")

class CaptionData(Base):
    __tablename__ = 'CaptionData'
    id = Column(Integer, primary_key=True)
    streamId = Column('StreamId', String)
    streamUrl = Column('StreamUrl', String)
    episodeId = Column(Integer, ForeignKey('episode.id'))
    episode = relationship('Episode', back_populates='captionData')

class WvKeyCache(Base):
    __tablename__ = 'WvKeyCache'
    id = Column(Integer, primary_key = True)
    pssh = Column('Pssh', String)
    key = Column('Key', String)