import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PySide6.QtCore import QStandardPaths

# Store database in user's AppData/Home folder just like before
user_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
DATA_DIR = os.path.join(user_data_path, "PythonPandaStudios", "PandaLedger")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Updated database name per the issue requirements
DB_FILE = os.path.join(DATA_DIR, "panda_ledger.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Create the SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Creates all tables defined in models that inherit from Base."""
    # We import the Base directly from schema where the tables are registered
    from models.schema import Base 
    Base.metadata.create_all(bind=engine)