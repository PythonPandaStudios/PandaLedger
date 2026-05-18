import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import toga

# Setup basic console logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

def get_database_path() -> str:
    """
    Resolves the OS-specific path for the SQLite database.
    Detects if running in a Briefcase/Toga context.
    """
    app = toga.App.app
    db_name = "panda_ledger.db"

    # Implement a path resolver that detects if it's running in a Briefcase context.
    if app is not None and hasattr(app, 'paths'):
        # SQLite connection string defaults to app.paths.data when running as a packaged app.
        data_dir = app.paths.data
    else:
        # On Desktop, we use local folders (Fallback for raw script execution)
        data_dir = os.path.join(os.path.expanduser("~"), ".pandaledger")

    # Ensure the directory actually exists before SQLite attempts to write
    os.makedirs(data_dir, exist_ok=True)
    
    return os.path.join(data_dir, db_name)

def init_database():
    """
    Initializes the database engine, configures WAL mode, and returns a session factory.
    """
    db_path = get_database_path()
    connection_string = f"sqlite:///{db_path}"

    # Initialize engine with thread-safety for GUI event loops
    engine = create_engine(
        connection_string,
        connect_args={"check_same_thread": False}, 
        echo=False
    )

    # Enforce explicit write-ahead logging (WAL mode) for data integrity
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    # --- THE FIX ---
    # Explicitly import the schema here so SQLAlchemy's Base registers 
    # the Transaction model BEFORE it attempts to create the tables.
    import pandaledger.models.schema 
    
    # Bind models
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Log a success message to the console verifying a successful connection
    logger.info(f"SUCCESS: Connected to database at {db_path}")
    
    return SessionLocal

# Global session factory
Session = init_database()