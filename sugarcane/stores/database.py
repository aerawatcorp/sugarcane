from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from stores import BaseStore

"""
TODO:
Store class for storing data in a database using SQLAlchemy
"""


class DatabaseStore(BaseStore):
    def __init__(self, config):
        # Connect to database using config
        self.engine = create_engine(config["engine"])
        Base = declarative_base()
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Define database model (same as before)
        class DataEntry(Base):
            __tablename__ = "data"
            id = Column(Integer, primary_key=True)
            payload = Column(String)

        # Initialize database (create table if not exists)
        Base.metadata.create_all(self.engine)

    def store(self, data):
        # Create new data entry
        new_entry = DataEntry(payload=data)

        # Add entry to database session
        session = self.SessionLocal()
        try:
            session.add(new_entry)
            session.commit()
            return True
        except Exception as e:
            # Handle database errors
            print(f"Error storing data: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get(self, oid):
        raise NotImplementedError

    def retrieve(self, filters=None):
        # Get all data entries from database
        session = self.SessionLocal()
        try:
            entries = session.query(DataEntry).all()
            return [entry.payload for entry in entries]
        except Exception as e:
            # Handle database errors
            print(f"Error retrieving data: {e}")
            return []
        finally:
            session.close()
