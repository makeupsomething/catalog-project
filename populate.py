from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from setup_db import Category, Base, Item, User

engine = create_engine('sqlite:///categoryanditems.db')
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

# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Add Categories
cat1 = Category(name="Soccer")

session.add(cat1)
session.commit()

cat2 = Category(name="Bouldering")

session.add(cat2)
session.commit()

item1 = Item(user_id=1, name="Soccer Ball", description="This is the ball that will be used in the 2018 world cup",
                     price="$7.50", category=cat1)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Soccer Boots", description="The same boots that Messi wears",
                     price="$17.50", category=cat1)

session.add(item2)
session.commit()

item3 = Item(user_id=1, name="Bouldering Shoes", description="A tight fit is better",
                     price="$13.50", category=cat2)

session.add(item3)
session.commit()