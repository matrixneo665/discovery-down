from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

fn = '/config/dplus.sqlite'

engine = create_engine(f"sqlite+pysqlite:///{fn}", echo=False, future=True)

Base = declarative_base()

sessionMaker = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

i = 0