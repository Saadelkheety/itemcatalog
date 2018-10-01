from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_imageattach.entity import Image, image_attachment


from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Main_Category(Base):
    __tablename__ = 'maincategory'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)

    @property
    def serialize(self):
        # Return object data in easily serializeable format
        return {
            'name': self.name,
            'id': self.id,
        }


class Sub_Category(Base):
    __tablename__ = 'subcategory'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    description = Column(String(250), nullable=False)
    main_id = Column(Integer, ForeignKey('maincategory.id'), nullable=False)
    maincategory = relationship(Main_Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    picture = image_attachment('ItemPicture')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'main_id': self.main_id,
        }


class ItemPicture(Base, Image):
    __tablename__ = 'item_picture'
    item_id = Column(Integer, ForeignKey('subcategory.id'), primary_key=True)
    subcategory = relationship('Sub_Category')


# User helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except error:
        return None


engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)
