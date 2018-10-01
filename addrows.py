from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Main_Category, Base, Sub_Category

engine = create_engine('sqlite:///database.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

name = Main_Category(name="Landmarks")
session.add(name)
session.commit()

name = Main_Category(name="Restaurants")
session.add(name)
session.commit()

name = Main_Category(name="Cafes")
session.add(name)
session.commit()

name = Main_Category(name="Coworking space")
session.add(name)
session.commit()

name = Main_Category(name="Cinemas")
session.add(name)
session.commit()

name = Main_Category(name="Parks")
session.add(name)
session.commit()

name = Main_Category(name="Stores")
session.add(name)
session.commit()

name = Main_Category(name="Markets")
session.add(name)
session.commit()

name = Main_Category(name="Clubs")
session.add(name)
session.commit()

name = Main_Category(name="Others")
session.add(name)
session.commit()

print ("added!")
