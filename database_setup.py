from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Main_Category(Base):
    __tablename__ = 'maincategory'
    id = Column(Integer, primary_key = True)
    name = Column(String(20), nullable = False)

class Sub_Category(Base):
    __tablename__ = 'subcategory'
    id = Column(Integer, primary_key = True)
    name = Column(String(20), nullable = False)
    description = Column(String(250), nullable = False)
    main_id = Column(Integer, ForeignKey('maincategory.id'), nullable=False)
    maincategory = relationship(Main_Category)

engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)
