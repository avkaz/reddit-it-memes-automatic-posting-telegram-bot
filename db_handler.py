from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class DBHandler:
    def __init__(self, database_url):
        # Create an SQLAlchemy engine and metadata
        self.engine = create_engine(database_url, echo=True)
        self.metadata = MetaData()

        # Define tables for memes and statistics
        self.memes_table = Table(
            'reddit_items',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('rank', Integer),
            Column('comments', Integer),
            Column('load_order', Integer),
            Column('url', String),
            Column('file_id', String),
            Column('signature', String),
            Column('posted_by', String),
            Column('posted_when', Integer),
            Column('date_added', Date),
            Column('checked', Boolean),
            Column('approved', Boolean),
            Column('published', Boolean),
            Column('my_comment', String)
        )

        self.stats_table = Table(
            'statistics',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('all_published_count', Integer),
            Column('all_deleted_count', Integer),
            Column('published_suggested_count', Integer),
            Column('published_manual_count', Integer),
            Column('max_rank_of_suggested', Integer),
            Column('min_rank_of_suggested', Integer),
            Column('mean_rank_of_suggested', Integer),
        )

        # Define declarative base classes for memes and statistics
        self.Base = declarative_base()

        class Meme(self.Base):
            __table__ = self.memes_table

        self.Meme = Meme

        class Statistics(self.Base):
            __table__ = self.stats_table

        self.Statistics = Statistics

    def get_meme_to_channel(self):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Query the database for an unchecked, approved, and unpublished meme
                query = session.query(self.Meme).filter_by(checked=True, approved=True, published=False).order_by(
                    self.Meme.rank.desc())
                meme = query.first()
                return meme

        except Exception as e:
            # Log an error message if an exception occurs during meme retrieval
            logging.error(f"Error getting meme: {e}")

    def mark_as_published(self, meme_id, status):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Query the database for the specified meme ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the published status and commit the changes
                    meme.published = status
                    session.commit()

        except Exception as e:
            # Log an error message if an exception occurs during marking as published
            logging.error(f"Error marking meme as published: {e}")

    def remove_old_memes(self, date):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Define a helper function for meme deletion
                def delete_memes(memes, log_prefix):
                    if memes:
                        # Log the number of memes to delete
                        logging.info(f"Found {len(memes)} {log_prefix} memes to delete.")

                        for meme in memes:
                            # Log the deletion of each meme and delete it
                            logging.info(f"Deleting {log_prefix.lower()} meme id: {meme.id}")
                            session.delete(meme)
                            logging.info(f"{log_prefix.capitalize()} meme id {meme.id} deleted successfully.")

                        # Commit the changes and log the completion of the deletion process
                        session.commit()
                        logging.info(f"{log_prefix.capitalize()} deletion process completed.")
                    else:
                        # Log a message if no memes are found to delete
                        logging.info(f"No {log_prefix.lower()} memes found to delete.")

                # Query the database for memes older than the specified date
                memes_to_delete = (
                    session.query(self.Meme)
                    .filter(self.Meme.date_added <= date, self.Meme.checked == True, self.Meme.approved == False)
                    .all()
                )

                # Query the database for posted memes older than the specified date
                posted_memes_to_delete = (
                    session.query(self.Meme)
                    .filter(self.Meme.date_added <= date, self.Meme.published == True)
                    .all()
                )

                # Use the helper function to delete memes
                delete_memes(memes_to_delete, "Unapproved")
                delete_memes(posted_memes_to_delete, "Posted")

                return len(memes_to_delete), len(posted_memes_to_delete)
        except Exception as e:
            # Log an error message if an exception occurs during the deletion process
            logging.error(f"An error occurred during the deletion process: {e}")
            return 0  # Return 0 or another appropriate value in case of an error


    def mark_as_checked(self, meme_id, status):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Query the database for the specified meme ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the checked status and commit the changes
                    meme.checked = status
                    session.commit()

        except Exception as e:
            # Log an error message if an exception occurs during marking as checked
            logging.error(f"Error marking meme as checked: {e}")

    def mark_as_approved(self, meme_id, status):
        try:
            # Create a session to interact with the database
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                # Query the database for the specified meme ID
                meme = session.query(self.Meme).filter_by(id=meme_id).first()

                if meme:
                    # Update the approved status and commit the changes
                    meme.approved = status
                    session.commit()

        except Exception as e:
            # Log an error message if an exception occurs during marking as approved
            logging.error(f"Error marking meme as approved: {e}")
